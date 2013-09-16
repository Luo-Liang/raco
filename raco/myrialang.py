# vim: tabstop=2 softtabstop=2 shiftwidth=2 expandtab
#
# The above modeline for Vim automatically sets it to
# .. Bill's Python style. If it doesn't work, check
#     :set modeline?        -> should be true
#     :set modelines?       -> should be > 0

import algebra
import boolean
import json
import rules
import scheme
import sys
from language import Language
from utility import emit

op_id = 0
def gen_op_id():
  global op_id
  op_id += 1
  return "operator%d" % op_id

def scheme_to_schema(s):
  names, descrs = zip(*s.asdict.items())
  names = ["%s" % n for n in names]
  types = [r[1] for r in descrs]
  return {"column_types" : types, "column_names" : names}

class MyriaLanguage(Language):
  reusescans = False

  @classmethod
  def new_relation_assignment(cls, rvar, val):
    return emit(cls.relation_decl(rvar), cls.assignment(rvar,val))

  @classmethod
  def relation_decl(cls, rvar):
    # no type declarations necessary
    return ""

  @staticmethod
  def assignment(x, y):
    return ""

  @staticmethod
  def comment(txt):
    #return  "# %s" % txt
    # comments not technically allowed in json
    return  ""

  @classmethod
  def boolean_combine(cls, args, operator="and"):
    opstr = " %s " % operator 
    conjunc = opstr.join(["%s" % cls.compile_boolean(arg) for arg in args])
    return "(%s)" % conjunc

  @staticmethod
  def mklambda(body, var="t"):
    return ("lambda %s: " % var) + body

  @staticmethod
  def compile_attribute(name):
    return '%s' % name

class MyriaOperator:
  language = MyriaLanguage

class MyriaScan(algebra.Scan, MyriaOperator):
  def compileme(self, resultsym):
    return {
        "op_name" : resultsym,
        "op_type" : "TableScan",
        "relation_key" : {
          "user_name" : "public",
          "program_name" : "adhoc",
          "relation_name" : self.relation.name
        }
      }

class MyriaSelect(algebra.Select, MyriaOperator):
  def compileme(self, resultsym, inputsym):
    return {
        "op_name" : resultsym,
        "op_type" : "SELECT",
        "condition" : self.language.compile_boolean(self.condition),
        "input" : inputsym
      }

class MyriaProject(algebra.Project, MyriaOperator):
  def compileme(self, resultsym, inputsym):
    cols = [x.position for x in self.columnlist]
    return {
        "op_name" : resultsym,
        "op_type" : "Project",
        "arg_field_list" : cols,
        "arg_child" : inputsym
      }

class MyriaInsert(algebra.Store, MyriaOperator):
  def compileme(self, resultsym, inputsym):
    return {
        "op_name" : resultsym,
        "op_type" : "DbInsert",
        "relation_key" : {
          "user_name" : "public",
          "program_name" : "adhoc",
          "relation_name" : self.name
        },
        "arg_overwrite_table" : True,
        "arg_child" : inputsym,
      }

class MyriaLocalJoin(algebra.ProjectingJoin, MyriaOperator):
  @classmethod
  def convertcondition(self, condition):
    """Convert the joincondition to a list of left columns and a list of right columns representing a conjunction"""


    if isinstance(condition, boolean.AND):
      leftcols1, rightcols1 = self.convertcondition(condition.left)
      leftcols2, rightcols2 = self.convertcondition(condition.right)
      return leftcols1 + leftcols2, rightcols1 + rightcols2

    if isinstance(condition, boolean.EQ):
      return [condition.left.position], [condition.right.position]

    raise NotImplementedError("Myria only supports EquiJoins")
  
  def compileme(self, resultsym, leftsym, rightsym):
    """Compile the operator to a sequence of json operators"""
  
    leftcols, rightcols = self.convertcondition(self.condition)

    if self.columnlist is None:
      self.columnlist = self.scheme().ascolumnlist()
    column_names = [name for (name,type) in self.scheme()]

    allleft = [i.position for i in self.columnlist if i.position < len(self.left.scheme())]
    allright = [i.position-len(self.left.scheme()) for i in self.columnlist if i.position >= len(self.left.scheme())]

    join = {
        "op_name" : resultsym,
        "op_type" : "LocalJoin",
        "arg_column_names" : column_names,
        "arg_child1" : "%s" % leftsym,
        "arg_columns1" : leftcols,
        "arg_child2": "%s" % rightsym,
        "arg_columns2" : rightcols,
        "arg_select1" : allleft,
        "arg_select2" : allright
      }

    return join

class MyriaShuffle(algebra.Shuffle, MyriaOperator):
  """Represents a simple shuffle operator"""
  def compileme(self, resultsym, inputsym):
    raise NotImplementedError('shouldn''t ever get here, should be turned into SP-SC pair')

class MyriaShuffleProducer(algebra.UnaryOperator, MyriaOperator):
  """A Myria ShuffleProducer"""
  def __init__(self, input, opid, hash_columns):
    algebra.UnaryOperator.__init__(self, input)
    self.opid = opid
    self.hash_columns = hash_columns

  def shortStr(self):
    hash_string = ','.join([str(x) for x in self.hash_columns])
    return "%s(h(%s), %s)" % (self.opname(), hash_string, self.opid)

  def compileme(self, resultsym, inputsym):
    if len(self.hash_columns) == 1:
      pf = {
          "type" : "SingleFieldHash",
          "index" : self.hash_columns[0]
        }
    else:
      pf = {
          "type" : "MultiFieldHash",
          "index" : self.hash_columns
        }

    return {
        "op_name" : resultsym,
        "op_type" : "ShuffleProducer",
        "arg_child" : inputsym,
        "arg_operator_id" : self.opid,
        "arg_pf" : pf
      }

class MyriaShuffleConsumer(algebra.UnaryOperator, MyriaOperator):
  """A Myria ShuffleConsumer"""
  def __init__(self, input, opid):
    algebra.UnaryOperator.__init__(self, input)
    self.opid = opid

  def compileme(self, resultsym, inputsym):
    return {
        'op_name' : resultsym,
        'op_type' : 'ShuffleConsumer',
        'arg_operator_id' : self.opid,
        'arg_schema' : scheme_to_schema(self.scheme())
      }

  def shortStr(self):
    return "%s(%s)" % (self.opname(), self.opid)


class BreakShuffle(rules.Rule):
  def fire(self, expr):
    if not isinstance(expr, MyriaShuffle):
      return expr

    opid = gen_op_id()
    producer = MyriaShuffleProducer(expr.input, opid, expr.columnlist)
    consumer = MyriaShuffleConsumer(producer, opid)
    return consumer

class ShuffleBeforeJoin(rules.Rule):
  def fire(self, expr):
    # If not a join, who cares?
    if not isinstance(expr, algebra.Join):
      return expr

    # If both have shuffles already, who cares?
    if isinstance(expr.left, algebra.Shuffle) and isinstance(expr.right, algebra.Shuffle):
      return expr

    # Convert to unnamed perspective
    condition = MyriaLanguage.unnamed(expr.condition, expr.scheme())

    # Figure out which columns go in the shuffle
    left_cols, right_cols = MyriaLocalJoin.convertcondition(expr.condition)

    # Left shuffle
    if isinstance(expr.left, algebra.Shuffle):
      left_shuffle = expr.left
    else:
      left_shuffle = algebra.Shuffle(expr.left, left_cols)
    # Right shuffle
    if isinstance(expr.right, algebra.Shuffle):
      right_shuffle = expr.right
    else:
      right_shuffle = algebra.Shuffle(expr.right, right_cols)

    # Construct the object!
    if isinstance(expr, algebra.ProjectingJoin):
      return algebra.ProjectingJoin(expr.condition, left_shuffle, right_shuffle, expr.columnlist)
    elif isinstance(expr, algebra.Join):
      return algebra.Join(expr.condition, left_shuffle, right_shuffle)
    raise NotImplementedError("How the heck did you get here?")

class ApplyHardcodedSchema(rules.Rule):
  """A rule to insert the hardcoded Myria schema for certain objects."""
  # TODO remove this and replace with a REST API lookup
  def fire(self, expr):
    hardcoded_schema = {
        'R': [('x', 'INT_TYPE'), ('y', 'INT_TYPE')],
        'R3': [('x', 'INT_TYPE'), ('y', 'INT_TYPE'), ('z', 'INT_TYPE')],
        'S': [('x', 'INT_TYPE'), ('y', 'INT_TYPE')],
        'S3': [('x', 'INT_TYPE'), ('y', 'INT_TYPE'), ('z', 'INT_TYPE')],
        'T': [('x', 'INT_TYPE'), ('y', 'INT_TYPE')],
        'T3': [('x', 'INT_TYPE'), ('y', 'INT_TYPE'), ('z', 'INT_TYPE')],
        'Twitter': [('followee', 'INT_TYPE'), ('follower', 'INT_TYPE')],
        'TwitterK': [('followee', 'INT_TYPE'), ('follower', 'INT_TYPE')],
    }
    # TODO only handles MyriaScan right now
    if not isinstance(expr, MyriaScan):
      # warn if zeroary
      if isinstance(expr, algebra.ZeroaryOperator):
        print >>sys.stderr, "warning, unhandled ZeroaryOperator %s" % type(expr)
      return expr
    try:
      expr.relation._scheme = scheme.Scheme(hardcoded_schema[expr.relation.name])
    except KeyError:
      # raise KeyError("Scanned relation %s has no hardcoded scheme!" % expr.relation.name)
      pass
    return expr

class MyriaAlgebra:
  language = MyriaLanguage

  operators = [
      MyriaLocalJoin
      , MyriaSelect
      , MyriaProject
      , MyriaScan
      , MyriaInsert
  ]

  fragment_leaves = (
      MyriaShuffleConsumer
      , MyriaScan
  )

  rules = [
      rules.ProjectingJoin()
      , rules.JoinToProjectingJoin()
      , ShuffleBeforeJoin()
      , rules.OneToOne(algebra.Store,MyriaInsert)
      , rules.OneToOne(algebra.Select,MyriaSelect)
      , rules.OneToOne(algebra.Shuffle,MyriaShuffle)
      , rules.OneToOne(algebra.Project,MyriaProject)
      , rules.OneToOne(algebra.ProjectingJoin,MyriaLocalJoin)
      , rules.OneToOne(algebra.Scan,MyriaScan)
      , BreakShuffle()
      , ApplyHardcodedSchema() # TODO replace with Catalog call
  ]

def compile_to_json(raw_query, logical_plan, physical_plan):
  """This function compiles a logical RA plan to the JSON suitable for
  submission to the Myria REST API server."""

  # A dictionary mapping each object to a unique, object-dependent symbol.
  # Since we want this to be truly unique for each object instance, even if two
  # objects are equal, we use id(obj) as the key.
  syms = {}

  def one_fragment(rootOp):
      """Given an operator that is the root of a query fragment/plan, extract
      the operators in the fragment. Assembles a list cur_frag of the operators
      in the current fragment, in preorder from the root.
      
      This operator also assembles a queue of the discovered roots of later
      fragments, e.g., when there is a ShuffleProducer below. The list of
      operators that should be treated as fragment leaves is given by
      MyriaAlgebra.fragment_leaves. """

      # The current fragment starts with the current root
      cur_frag = [rootOp]
      # If necessary, assign a symbol to the root operator
      if id(rootOp) not in syms:
          syms[id(rootOp)] = algebra.gensym()
      # Initially, there are no new roots discovered below leaves of this
      # fragment.
      queue = []
      if isinstance(rootOp, MyriaAlgebra.fragment_leaves):
          # The current root operator is a fragment leaf, such as a
          # ShuffleProducer. Append its children to the queue of new roots.
          for child in rootOp.children():
              queue.append(child)
      else:
          # Otherwise, the children belong in this fragment. Recursively go
          # discover their fragments, including the queue of roots below their
          # children.
          for child in rootOp.children():
              (child_frag, child_queue) = one_fragment(child)
              # Add their fragment onto this fragment
              cur_frag += child_frag
              # Add their roots-of-next-fragments into our queue
              queue += child_queue
      return (cur_frag, queue)

  def fragments(rootOp):
      """Given the root of a query plan, recursively determine all the fragments
      in it."""
      # The queue of fragment roots. Initially, just the root of this query
      queue = [rootOp]
      ret = []
      while len(queue) > 0:
          # Get the next fragment root
          rootOp = queue.pop(0)
          # .. recursively learn the entire fragment, and any newly discovered
          # roots.
          (op_frag, op_queue) = one_fragment(rootOp)
          # .. Myria JSON expects the fragment operators in reverse order,
          # i.e., root at the bottom.
          ret.append(reversed(op_frag))
          # .. and collect the newly discovered fragment roots.
          queue.extend(op_queue)
      return ret

  def call_compile_me(op):
      "A shortcut to call the operator's compile_me function."
      opsym = syms[id(op)]
      childsyms = [syms[id(child)] for child in op.children()]
      if isinstance(op, algebra.ZeroaryOperator):
          return op.compileme(opsym)
      if isinstance(op, algebra.UnaryOperator):
          return op.compileme(opsym, childsyms[0])
      if isinstance(op, algebra.BinaryOperator):
          return op.compileme(opsym, childsyms[0], childsyms[1])
      if isinstance(op, algebra.NaryOperator):
          return op.compileme(opsym, childsyms)
      raise NotImplementedError("unable to handle operator of type "+type(op))

  # The actual code. all_frags collects up the fragments.
  all_frags = []
  # For each IDB, generate a plan that assembles all its fragments and stores
  # them back to a relation named (label).
  for (label, rootOp) in physical_plan:
      if isinstance(rootOp, algebra.Store):
          # If there is already a store (including MyriaInsert) at the top, do
          # nothing.
          frag_root = rootOp
      else:
          # Otherwise, add an insert at the top to store this relation to a
          # table named (label).
          frag_root = MyriaInsert(plan=rootOp, name=label)
      # Make sure the root is in the symbol dictionary, but rather than using a
      # generated symbol use the IDB label.
      syms[id(frag_root)] = label
      # Determine the fragments.
      frags = fragments(frag_root)
      # Build the fragments.
      all_frags.extend([{'operators': [call_compile_me(op) for op in frag]} for frag in frags])
      # Clear out the symbol dictionary for the next IDB.
      syms.clear()

  # Assemble all the fragments into a single JSON query plan
  query = {
          'fragments' : all_frags,
          'raw_datalog' : raw_query,
          'logical_ra' : str(logical_plan)
          }
  return query
from utility import Printable

"""
Boolean logic
"""

class BooleanExpression(Printable):
  pass

'''
# not supported, and not necessary
class BooleanLiteral(BooleanExpression):
  pass

class BTrue(BooleanLiteral):
  literals = ["True", "true", "TRUE"]

class BFalse(BooleanLiteral):
  literals = ["False", "false", "FALSE"]
'''

class BinaryBooleanOperator(BooleanExpression):
  def __init__(self, left, right):
    self.left = left
    self.right = right

  def __str__(self):
    if not hasattr(self, "literals"):
      opstr = self.opname()
    else:
     opstr = self.literals[0]
    return "%s %s %s" % (self.left, opstr, self.right)

  def __repr__(self):
    return self.__str__()

  def leftoffset(self, offset):
    """Add an offset to any positional references on the left-hand side.  Useful when constructing left-deep plans."""
    self.left.leftoffset(offset)
    self.right.leftoffset(offset)

  def rightoffset(self, offset):
    """Add an offset to any positional references on the left-hand side.  Useful when constructing right-deep plans."""
    self.left.rightoffset(offset)
    self.right.rightoffset(offset)

  def flip(self):
    """flip the order of comparison operators.  Used in optimizing join trees"""
    self.left.flip()
    self.right.flip()

class BinaryComparisonOperator(BinaryBooleanOperator):
  def flip(self):
    """Return a new condition that reverses the direction of this condition. 
E.g., 3>X becomes X<3. Useful for normalizing plans."""
    return reverse[self.__class__](self.right, self.left)

  def leftoffset(self, offset):
    """Add an offset to any positional references on the left-hand side.  Useful when constructing left-deep plans."""
    self.left.leftoffset(offset)
    
  def rightoffset(self, offset):
    """Add an offset to any positional references on the left-hand side.  Useful when constructing right-deep plans."""
    self.right.rightoffset(offset)

class AND(BinaryBooleanOperator):
  literals = ["and", "AND"]

class OR(BinaryBooleanOperator):
  literals = ["or", "OR"]

class EQ(BinaryComparisonOperator):
  literals = ["=", "=="]

class LT(BinaryComparisonOperator):
  literals = ["<", "lt"]

class GT(BinaryComparisonOperator):
  literals = [">", "gt"]

class GTEQ(BinaryComparisonOperator):
  literals = [">=", "gteq", "gte"]

class LTEQ(BinaryComparisonOperator):
  literals = ["<=", "lteq", "lte"]

class NEQ(BinaryComparisonOperator):
  literals = ["!=", "neq", "ne"]

reverse = {
  NEQ:NEQ,
  EQ:EQ,
  GTEQ:LTEQ,
  LTEQ:GTEQ,
  GT:LT,
  LT:GT
}

complement = {
  NEQ:EQ,
  EQ:NEQ,
  GTEQ:LT,
  LTEQ:GT,
  GT:LTEQ,
  LT:GTEQ
}

class Literal:
  def __init__(self, value):
    self.value = value

  def __repr__(self):
    return str(self.value)

  def leftoffset(self, offset):
    """Add an offset to any positional references on the left-hand side.  Useful when constructing left-deep plans."""
    pass

  def rightoffset(self, offset):
    """Add an offset to this positional reference.  Used when building a plan from a set of joins"""
    pass 

class StringLiteral(Literal):
  pass

class NumericLiteral(Literal):
  pass

class AttributeReference:
  """A reference to an attribute. Aware of the schema and the query structure
in order to implement either the named or unnamed perspective. 
Will subsume PositionReference and Attribute"""
  def __init__(self, ):
    self.name = value

class PositionReference(AttributeReference):
  """A reference to an attribute by position, for implementing the unnamed perspective."""
  def __init__(self, position):
    self.position = position   

  def leftoffset(self, offset):
    """Add an offset to this positional reference.  Used when building a plan from a set of joins"""
    self.position = self.position + offset

  def rightoffset(self, offset):
    """Add an offset to this positional reference.  Used when building a plan from a set of joins"""
    self.position = self.position + offset

  def __repr__(self):
    return "col%s" % self.position

  def compile(self):
    return self.position

  def resolve(self, scheme):
    return scheme[self.position]


class Attribute(AttributeReference):
  """A reference to an attribute by name"""
  def __init__(self, value):
    self.name = value

  def __repr__(self):
    return str(self.name)

  def compile(self):
    return self.name

  def resolve(self, scheme):
    return scheme[self.name]

def toUnnamed(ref, scheme):
  """Convert a reference to the unnamed perspective"""
  if issubclass(ref, PositionReference):
    return ref
  elif issubclass(ref, Attribute):
    return PositionReference(scheme.getpos(ref.name))
  else:
    raise TypeError("Unknown value reference %s.  Expected a position reference or an attribute reference.")

def toNamed(ref, scheme):
  """Convert a reference to the named perspective"""
  if issubclass(ref, PositionReference):
    attrname = scheme[ref.position][0]
    return Attribute(attrname)
  elif issubclass(ref, Attribute):
    return ref
  else:
    raise TypeError("Unknown value reference %s.  Expected a position reference or an attribute reference.")
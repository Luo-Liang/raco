#!/usr/bin/python

import raco.myrial.parser as parser
import raco.algebra
import raco.catalog

import collections
import random
import sys
import types

class ExpressionProcessor:
    '''Convert syntactic expressions into a relational algebra operation'''
    def __init__(self, symbols):
        self.symbols = symbols

    def evaluate(self, expr):
        method = getattr(self, expr[0].lower())
        return method(*expr[1:])

    def alias(self, _id):
        return self.symbols[_id]

    def scan(self, relation_key, scheme):
        # TODO(AJW) resolve the schema if it's not provided
        assert scheme # REMOVE THIS!

        # TODO(AJW): Use the entire relation key!
        rel = raco.catalog.Relation(relation_key.table, scheme)
        return raco.algebra.Scan(rel)

    def load(self, path, schema):
        pass

    def table(self, tuple_list, schema):
        pass

    def distinct(self, _id):
        pass

    def __process_bitop(self, _type, id1, id2):
        c_op1 = self.symbols[id1]
        c_op2 = self.symbols[id2]
        pass

    def union(self, id1, id2):
        return self.__process_bitop('UNION', id1, id2)

    def intersect(self, id1, id2):
        return self.__process_bitop('INTERSECT', id1, id2)

    def diff(self, id1, id2):
        return self.__process_bitop('DIFF', id1, id2)

    def limit(self, _id, count):
        c_op1 = self.symbols[_id]
        pass

    def join(self, arg1, arg2):
        c_op1 = self.symbols[arg1.id]
        c_op2 = self.symbols[arg2.id]
        pass

class StatementProcessor:
    '''Evaluate a list of statements'''

    def __init__(self, out=sys.stdout, eager_evaluation=False):
        # Map from identifiers to db operation
        self.symbols = {}
        self.ep = ExpressionProcessor(self.symbols)

    def evaluate(self, statements):
        '''Evaluate a list of statements'''
        for statement in statements:
            # Switch on the first tuple entry
            method = getattr(self, statement[0].lower())
            method(*statement[1:])

    def assign(self, _id, expr):
        '''Assign to a variable by modifying the symbol table'''
        op = self.ep.evaluate(expr)
        self.symbols[_id] = op

    def explain(self, _id):
        '''Dump the logical query plan for an identifier'''
        op = self.symbols[_id]

        if type(self.out) == types.ListType:
            self.out.append(op)
        else:
            s = '%s : %s\n' % (_id, str(op))
            self.out.write(s)

    def describe(self, _id):
        pass

    def dump(self, _id):
        pass

    def dowhile(self, statement_list, termination_ex):
        pass

def evaluate(s, out=sys.stdout):
    _parser = parser.Parser()
    processor = StatementProcessor(out)

    statement_list = _parser.parse(s)
    processor.evaluate(statement_list)

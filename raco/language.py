from raco import expression

from abc import ABCMeta, abstractmethod

import logging
LOG = logging.getLogger(__name__)


class Language(object):
    __metaclass__ = ABCMeta

    # By default, reuse scans
    reusescans = True

    @staticmethod
    def preamble(query=None, plan=None):
        return ""

    @staticmethod
    def postamble(query=None, plan=None):
        return ""

    @staticmethod
    def body(compileResult):
        return compileResult

    @classmethod
    def compile_stringliteral(cls, value):
        return '"%s"' % value

    @staticmethod
    def log(txt):
        """Emit code that will generate a log message at runtime. Defaults to
        nothing."""
        return ""

    @classmethod
    def compile_numericliteral(cls, value):
        return '%s' % value

    @classmethod
    def compile_attribute(cls, attr):
        return attr.compile()

    @classmethod
    def conjunction(cls, *args):
        return cls.expression_combine(args, operator="and")

    @classmethod
    def disjunction(cls, *args):
        return cls.expression_combine(args, operator="or")

    @classmethod
    def unnamed(cls, condition, sch):
        LOG.debug("unnamed %s %s %s", cls, condition, sch)
        """
    Replace column names with positions
    """
        if isinstance(condition, expression.BinaryBooleanOperator):
            condition.left = Language.unnamed(condition.left, sch)
            condition.right = Language.unnamed(condition.right, sch)
            result = condition

        elif isinstance(condition, expression.UnaryBooleanOperator):
            condition.input = Language.unnamed(condition.input, sch)
            result = condition

        elif isinstance(condition, expression.NamedAttributeRef):
            pos = sch.getPosition(condition.name)
            result = expression.UnnamedAttributeRef(pos)
        elif isinstance(condition, expression.UnnamedAttributeRef):
            result = condition
        else:
            # do nothing; it's a literal or something custom
            result = condition

        return result

    @classmethod
    def compile_expression(cls, expr):
        compilevisitor = CompileExpressionVisitor(cls)
        expr.accept(compilevisitor)
        return compilevisitor.getresult()

    @classmethod
    @abstractmethod
    def expression_combine(cls, args, operator="and"):
        """Combine the given arguments using the specified infix operator"""


class CompileExpressionVisitor(expression.ExpressionVisitor):
    def __init__(self, language):
        self.language = language
        self.combine = language.expression_combine
        self.stack = []

    def getresult(self):
        assert len(self.stack) == 1
        return self.stack.pop()

    def __visit_BinaryOperator__(self, binaryexpr):
        right = self.stack.pop()
        left = self.stack.pop()
        return left, right

    def visit_NOT(self, unaryexpr):
        inputexpr = self.stack.pop()
        self.stack.append(self.language.negation(inputexpr))

    def visit_AND(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.language.conjunction(left, right))

    def visit_OR(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.language.disjunction(left, right))

    def visit_EQ(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="=="))

    def visit_NEQ(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="!="))

    def visit_GT(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator=">"))

    def visit_LT(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="<"))

    def visit_GTEQ(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator=">="))

    def visit_LTEQ(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="<="))

    def visit_NamedAttributeRef(self, named):
        self.stack.append(self.language.compile_attribute(named))

    def visit_UnnamedAttributeRef(self, unnamed):
        LOG.debug("expr %s is UnnamedAttributeRef", unnamed)
        self.stack.append(self.language.compile_attribute(unnamed))

    def visit_NumericLiteral(self, numericliteral):
        self.stack.append(self.language.compile_numericliteral(numericliteral))

    def visit_StringLiteral(self, stringliteral):
        self.stack.append(self.language.compile_stringliteral(stringliteral))

    def visit_DIVIDE(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="/"))

    def visit_PLUS(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="+"))

    def visit_MINUS(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="-"))

    def visit_IDIVIDE(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="/"))

    def visit_TIMES(self, binaryexpr):
        left, right = self.__visit_BinaryOperator__(binaryexpr)
        self.stack.append(self.combine([left, right], operator="*"))

    def visit_NEG(self, unaryexpr):
        inputexpr = self.stack.pop()
        self.stack.append(self.language.negative(inputexpr))


# import everything from each language
from raco.pythonlang import PythonAlgebra
from raco.pseudocodelang import PseudoCodeAlgebra
from raco.clang import CCAlgebra
from raco.myrialang import MyriaLeftDeepTreeAlgebra
from raco.myrialang import MyriaHyperCubeAlgebra
from raco.grappalang import GrappaAlgebra

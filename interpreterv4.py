# Author: Shelby Falde
# Course: CS131

from brewparse import *
from intbase import *

import sys
sys.tracebacklimit = 0

import copy
nil = Element("nil")

# Source: https://www.cs.virginia.edu/~evans/cs150/book/ch13-laziness-0402.pdf (Given on campuswire)
class Thunk:
    # expr stores the expression_node, env stores the variable scope.
    def __init__(self, expr, environment, evaluate_expression):
        self._expr = expr
        self._env = [copy.deepcopy(env) for env in environment]
        self._evaluated = False
        self._value = None
        self._evaluate_expression = evaluate_expression # Pass in expression eval method from Interpreter class
        #print(f"Initializing with environment: {self._env}")
        #print(f"Which was deepcopied from: {environment}")
        #print(f"{self}")
    
    def value(self):
        if not self._evaluated:
            self._value = self._evaluate_expression(self._expr, self._env)
            self._prev_value = self._value
            #print(f"Is now: {self._value}")
            self._evaluated = True
        return self._value
def isThunk(expr):
    return isinstance(expr, Thunk)

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        # Since functions (at the top level) can be created anywhere, we'll just do a search for function definitions and assign them 'globally'
        self.func_defs = []
        self.variable_scope_stack = [{}] # Stack to hold variable scopes
        
    def run(self, program):
        ast = parse_program(program) # returns list of function nodes
        #self.output(ast) # always good for start of assignment
        self.func_defs = self.get_func_defs(ast)
        main_func_node = self.get_main_func_node(ast)
        result = self.run_func(main_func_node) # change to do_func_call?
        #self.output(f"Program returned: {result}")
        # Check output status of program. - Does program result in a raised error?
        if isinstance(result, tuple) and result[1] == "error":
            exception, status = result
            super().error(ErrorType.FAULT_ERROR, f"",)

    # grabs all globally defined functions to call when needed.
    def get_func_defs(self, ast):
        # returns functions sub-dict, 'functions' is key
        return ast.dict['functions']

    # returns 'main' func node from the dict input.
    def get_main_func_node(self, ast):
        # checks for function whose name is 'main'
        for func in self.func_defs:
            if func.dict['name'] == "main":
                return func
        # define error for 'main' not found.
        super().error(ErrorType.NAME_ERROR, "No main() function was found",)

    # self explanatory
    def run_func(self, func_node, env=None):
        if env is None:
            env = self.variable_scope_stack
        # statements key for sub-dict.
        ### BEGIN FUNC SCOPE ###
        env.append({})
        return_value = nil
        for statement in func_node.dict['statements']:
            #self.output(f"Running statement: {statement}")
            #self.output(f"Env in run_func: {env}")
            return_value = self.run_statement(statement, env)
            #self.output(f"Statement: {statement}")
            # check if statement results in a return, and return a return statement with 
            if isinstance(return_value, Element) and return_value.elem_type == "return":
                env.pop() ## END FUNC SCOPE ##
                
                return_value = return_value.get("value")
                return return_value
            if isinstance(return_value, tuple) and return_value[1] == "error":
                break; # Don't run anymore statements, exit the clause immediately.
        
        ### END FUNC SCOPE ###
        env.pop()
        return return_value # (may return (exception, status))
    
    def run_statement(self, statement_node, env=None):
        if env is None:
            env = self.variable_scope_stack
        if self.is_definition(statement_node):
            self.do_definition(statement_node)
        elif self.is_assignment(statement_node):
            self.do_assignment(statement_node,env)
        elif self.is_func_call(statement_node):
            return self.do_func_call(statement_node, env)
        elif self.is_return_statement(statement_node):
            return self.do_return_statement(statement_node, env)
        elif self.is_if_statement(statement_node):
            return self.do_if_statement(statement_node, env)
        elif self.is_for_loop(statement_node):
            return self.do_for_loop(statement_node, env)
        elif self.is_raise_statement(statement_node):
            return self.do_raise_statement(statement_node, env)
        return nil
    
    def is_definition(self, statement_node):
        return (True if statement_node.elem_type == "vardef" else False)
    def is_assignment(self, statement_node):
        return (True if statement_node.elem_type == "=" else False)
    def is_func_call(self, statement_node):
        return (True if statement_node.elem_type == "fcall" else False)
    def is_return_statement(self, statement_node):
        return (True if statement_node.elem_type == "return" else False)
    def is_if_statement(self, statement_node):
        return (True if statement_node.elem_type == "if" else False)
    def is_for_loop(self, statement_node):
        return (True if statement_node.elem_type == "for" else False)
    def is_raise_statement(self, statement_node):
        return (True if statement_node.elem_type == "raise" else False)

    def do_definition(self, statement_node):
        # just add to var_name_to_value dict
        target_var_name = self.get_target_variable_name(statement_node)
        if target_var_name in self.variable_scope_stack[-1]:
            super().error(ErrorType.NAME_ERROR, f"Variable {target_var_name} defined more than once",)
        else:
            self.variable_scope_stack[-1][target_var_name] = None
        
    # env is either an environment or self.variable_scope_stack
    def do_assignment(self, statement_node, env):
        target_var_name = self.get_target_variable_name(statement_node)
        source_node = self.get_expression_node(statement_node)
        for scope in reversed(self.variable_scope_stack): 
            if target_var_name in scope: 
                scope[target_var_name] = Thunk(source_node, env, self.evaluate_expression) # Thunk deepcopys on init. now 
                return
        super().error(ErrorType.NAME_ERROR, f"variable used and not declared: {target_var_name}",)

    # Check if function is defined
    def check_valid_func(self, func_call):
        for func in self.func_defs:
            if func.dict['name'] == func_call:
                return True
        return False

    # Allows function overloading by first searching for func_defs for a matching name and arg length
    def get_func_def(self, func_call, arg_len):
        for func in self.func_defs:
            if func.dict['name'] == func_call and len(func.dict['args']) == arg_len:
                return func
        # Already check if func exists before calling
        # So, must not have correct args.
        super().error(ErrorType.NAME_ERROR,
                       f"Incorrect amount of arguments given: {arg_len} ",
                       )
    
    def do_func_call(self, statement_node, env=None):
        if env is None:
            env = self.variable_scope_stack

        func_call = statement_node.dict['name']
        if func_call == "print":
            output = ""
            # loop through each arg in args list for print, evaluate their expressions, concat, and output.
            for arg in statement_node.dict['args']:
                eval = self.evaluate_expression(arg, env)
                if isThunk(eval):
                    eval = eval.value()
                if self.check_if_returns_raised_error(eval): # propagate error on eval
                    return eval
                if type(eval) is bool:
                    if eval:
                        output += "true"
                    else: 
                        output += "false"
                else:
                    output += str(eval)
            # THIS IS 1/3 OF ONLY REAL SELF.OUTPUT
            self.output(output)
            return nil
        elif func_call == "inputi":
            # too many inputi params
            if len(statement_node.dict['args']) > 1:
                super().error(ErrorType.NAME_ERROR,f"No inputi() function found that takes > 1 parameter",)
            elif len(statement_node.dict['args']) == 1:
                arg = statement_node.dict['args'][0]
                # THIS IS 2/3 OF ONLY REAL SELF.OUTPUT
                eval = self.evaluate_expression(arg, env)
                if isThunk(eval):
                    eval = eval.value()
                if self.check_if_returns_raised_error(eval): # propagate error on eval
                    return eval
                self.output(eval)
            user_in = super().get_input()
            try:
                user_in = int(user_in)
                return user_in
            except:
                return user_in
        
        # same as inputi but for strings
        elif func_call == "inputs":
            # too many inputi params
            if len(statement_node.dict['args']) > 1:
                super().error(ErrorType.NAME_ERROR,f"No inputs() function found that takes > 1 parameter",)
            elif len(statement_node.dict['args']) == 1:
                arg = statement_node.dict['args'][0]
                # THIS IS 3/3 OF ONLY REAL SELF.OUTPUT
                eval = self.evaluate_expression(arg, env)
                if isThunk(eval):
                    eval = eval.value()
                if self.check_if_returns_raised_error(eval): # propagate error on eval
                    return eval
                self.output(eval)
            user_in = super().get_input()
            try:
                user_in = str(user_in)
                return user_in
            except:
                return user_in
        else:
            ## USER-DEFINED FUNCTION ##
            if not self.check_valid_func(func_call):
                super().error(ErrorType.NAME_ERROR,
                                f"Function {func_call} was not found",
                                )
            func_def = self.get_func_def(func_call, len(statement_node.dict['args']))
            ##### Start Function Call ######

            #### START FUNC SCOPE ####
            args = statement_node.dict['args'] # passed in arguments
            params = func_def.dict['args'] # function parameters
            processed_args = [{}]

            #self.output("Testing!")
            for i in range(0,len(params)):
                param_name = params[i].dict['name']
                arg_expr = args[i]
                arg_value = Thunk(arg_expr, env, self.evaluate_expression)
                processed_args[-1][param_name] = arg_value
            
            old_env = env.copy()
            env = processed_args
            return_value = self.run_func(func_def, env)
            
            #### END FUNC SCOPE ####
            env = old_env.copy()
            return return_value          
            ##### End Function Call ######
    
    def do_return_statement(self, statement_node ,env=None):
        
        if env is None:
            env = self.variable_scope_stack
        if not statement_node.dict['expression']:
            #return 'nil' Element
            return Element("return", value=nil)
        
        return self.evaluate_expression(statement_node.dict['expression'], env)

    # Scope rules: Can access parent calling vars, but vars they create are deleted after scope.
    # So, keep track of what vars were before, and after end of clause, wipe those variables.
    def do_if_statement(self, statement_node, env):
        if env is None:
            env = self.variable_scope_stack
        condition = statement_node.dict['condition']
        condition = self.evaluate_expression(condition, env)
        if isThunk(condition):
            condition = condition.value()
        if self.check_if_returns_raised_error(condition):
            return condition
        # error if condition is non-boolean
        if type(condition) is not bool:
            super().error(ErrorType.TYPE_ERROR, "Condition is not of type bool",)
        statements = statement_node.dict['statements']
        else_statements = statement_node.dict['else_statements']

        ### BEGIN IF SCOPE ###
        env.append({})
        if condition:
            for statement in statements:
                return_value = self.run_statement(statement, env)     
                if isinstance(return_value, Element) and return_value.elem_type == "return":
                    #end scope early and return
                    env.pop()
                    return Element("return", value=return_value.get("value"))
                elif return_value is not nil:
                    env.pop()
                    return Element("return", value=return_value)
                    # if return needed, stop running statements, immediately return the value.
        else:
            if else_statements:
                for else_statement in else_statements:
                    return_value = self.run_statement(else_statement, env)
                    
                    if isinstance(return_value, Element) and return_value.elem_type == "return":
                        #end scope early and return
                        env.pop()
                        return Element("return", value=return_value.get("value"))
                    elif return_value is not nil:
                        env.pop()
                        return Element("return", value=return_value)
        ### END IF SCOPE ###
        env.pop()
        return nil

    def do_for_loop(self, statement_node, env):
        # Run initializer
        init_node = statement_node.dict['init']
        self.run_statement(init_node, env)
        update = statement_node.dict['update']
        condition = statement_node.dict['condition']
        statements = statement_node.dict['statements']
        cond = True
        # Run the loop again (exits on condition false)
        while cond:
            cond = self.evaluate_expression(condition, env) 
            if isThunk(cond):
                cond = cond.value() # eagerly evaluate!
            if self.check_if_returns_raised_error(cond):
                return cond
            if type(cond) is not bool:
                super().error(ErrorType.TYPE_ERROR, "Condition is not of type bool",)
            if not cond:
                break
            ### BEGIN VAR SCOPE ###
            env.append({})

            for statement in statements:
                return_value = self.run_statement(statement, env)
                #self.output(f"statement in for loop returned {return_value}")
                # if return keyword
                if isinstance(return_value, Element) and return_value.elem_type == "return":

                    #end scope early and return
                    env.pop()
                    return Element("return", value=return_value.get("value"))
                elif return_value is not nil:
                    return Element("return", value=return_value)

            ### END VAR SCOPE ###
            env.pop()

            self.run_statement(update, env)
        return nil
        
    def do_raise_statement(self, statement_node, env):
        status = "error"
        #Eagerly evaluate exception type
        exception_type = statement_node.dict['exception_type']
        # Exception_type is a list of args
        exception = self.evaluate_expression(exception_type, env)
        if self.check_if_returns_raised_error(exception):
            return exception
        if not isinstance(exception, str):
            super().error(ErrorType.TYPE_ERROR, f"Exception '{exception}' does not evaluate to a string.",)

        #self.output(f"Raised exception: {(exception, status)}")
        return (exception, status)

    # Checks if eager evaluation returns 
    def check_if_returns_raised_error(self, eval):
        if isinstance(eval, tuple):
            exception, status = eval
            if status == "error":
                return True

    ## END OF STATEMENT NODES

    def get_target_variable_name(self, statement_node):
        return statement_node.dict['name']
    def get_expression_node(self, statement_node):
        return statement_node.dict['expression']
    
    # basically pseudocode, self-explanatory
    def is_value_node(self, expression_node):
        return True if (expression_node.elem_type in ["int", "string", "bool", "nil"]) else False
    def is_variable_node(self, expression_node):
        return True if (expression_node.elem_type == "var") else False
    def is_binary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["+", "-", "*", "/"]) else False
    def is_unary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["neg", "!"]) else False
    def is_comparison_operator(self, expression_node):
        return True if (expression_node.elem_type in ['==', '<', '<=', '>', '>=', '!=']) else False
    def is_binary_boolean_operator(self, expression_node):
        return True if (expression_node.elem_type in ['&&', '||']) else False

    # basically pseudcode, self-explanatory
    def evaluate_expression(self, expression_node, env=None): # default for env if none passed in
        if env is None:
            env = self.variable_scope_stack
        #if isThunk(expression_node):
        #    return expression_node.value()
        elif self.is_value_node(expression_node):
            return self.get_value(expression_node)
        elif self.is_variable_node(expression_node):
            return self.get_value_of_variable(expression_node,env)
        elif self.is_binary_operator(expression_node):
            return self.evaluate_binary_operator(expression_node,env)
        elif self.is_unary_operator(expression_node):
            return self.evaluate_unary_operator(expression_node,env)
        elif self.is_comparison_operator(expression_node):
            return self.evaluate_comparison_operator(expression_node, env)
        elif self.is_binary_boolean_operator(expression_node):
            return self.evaluate_binary_boolean_operator(expression_node, env)
        elif self.is_func_call(expression_node):
            return self.do_func_call(expression_node, env)

    def get_value(self, expression_node):
        # Returns value assigned to key 'val'
        if expression_node.elem_type == "nil":
            return nil
        return expression_node.dict['val']

    # returns value under the variable name provided.
    # NOTE: IF THIS FUNCTION IS CALLED, THAT MEANS WE EAGERLY EVALUATE, SO EVALUATE RELEVANT THUNKS.
    def get_value_of_variable(self, expression_node,env): 
        if expression_node == 'nil':
            return nil
        var_name = expression_node.dict['name']
        for scope in reversed(env):
        #for scope in reversed(self.variable_scope_stack): 
            if var_name in scope: 
                val = scope[var_name] 
                if val is None:
                    super().error(ErrorType.NAME_ERROR, f"variable '{var_name}' declared but not defined",)
                elif isThunk(val):
                    val = val.value() # So we dont print the thunk object + forces evaluation.
                    #self.output(f"Environment: {env}")
                return val 
        # if varname not found
        #self.output(f"Environment: {env}")
        #self.output(f"Scope stack: {self.variable_scope_stack}")
        super().error(ErrorType.NAME_ERROR, f"variable '{var_name}' used and not declared",)

    # + or -
    def evaluate_binary_operator(self, expression_node, env):
        # can *only* be +, -, *, / for now.
        eval1 = self.evaluate_expression(expression_node.dict['op1'], env)
        if self.check_if_returns_raised_error(eval1):
            return eval1
        eval2 = self.evaluate_expression(expression_node.dict['op2'], env)
        if self.check_if_returns_raised_error(eval2):
            return eval2
        #self.output(expression_node)
        #self.output(f"eval1: {eval1} eval2: {eval2}")

        # for all operators other than + (for concat), both must be of type 'int'
        if (expression_node.elem_type != "+") and not (type(eval1) == int and type(eval2) == int):
            super().error(ErrorType.TYPE_ERROR, "Arguments must be of type 'int'.",)
        if (expression_node.elem_type == "+") and not ((type(eval1) == int and type(eval2) == int) or (type(eval1) == str and type(eval2) == str)):
            super().error(ErrorType.TYPE_ERROR, "Types for + must be both of type int or string.",)
        if expression_node.elem_type == "+":
            return (eval1 + eval2)
        elif expression_node.elem_type == "-":
            return (eval1 - eval2)
        elif expression_node.elem_type == "*":
            return (eval1 * eval2)
        elif expression_node.elem_type == "/":
            if eval2 == 0:
                return("div0", "error") # return divide by 0 error
            # integer division
            return (eval1 // eval2)

    def evaluate_unary_operator(self, expression_node, env):
        # can be 'neg' (-b) or  '!' for boolean
        eval = self.evaluate_expression(expression_node.dict['op1'], env)
        if self.check_if_returns_raised_error(eval):
            return eval
        if expression_node.elem_type == "neg":
            if not (type(eval) == int):
                super().error(ErrorType.TYPE_ERROR, "'negation' can only be used on integer values.",)
            return -(eval)
        if expression_node.elem_type == "!":
            if not (type(eval) == bool):
                super().error(ErrorType.TYPE_ERROR, "'Not' can only be used on boolean values.",)
            return not (eval)
        
    # there's probably a better way to do this but oh well
    def evaluate_comparison_operator(self, expression_node, env):
        eval1 = self.evaluate_expression(expression_node.dict['op1'], env)
        if self.check_if_returns_raised_error(eval1):
            return eval1
        eval2 = self.evaluate_expression(expression_node.dict['op2'], env)
        if self.check_if_returns_raised_error(eval2):
            return eval2
        # != and == can compare different types.
        #self.output(f"eval1: {eval1} eval2: {eval2}")
        if (expression_node.elem_type not in ["!=", "=="]) and not (type(eval1) == int and type(eval2) == int):
            super().error(ErrorType.TYPE_ERROR, f"Comparison args for {expression_node.elem_type} must be of same type int.",)
        match expression_node.elem_type:
            case '<':
                return (eval1 < eval2)
            case '<=':
                return (eval1 <= eval2)
            case '==':
                if not (type(eval1) == type(eval2)):
                    return False
                else:
                    return (eval1 == eval2)
            case '>=':
                return (eval1 >= eval2)
            case '>':
                return (eval1 > eval2)
            case '!=': 
                if not (type(eval1) == type(eval2)):
                    return True
                else:
                    return (eval1 != eval2)
    
    def evaluate_binary_boolean_operator(self, expression_node, env):
        eval1 = self.evaluate_expression(expression_node.dict['op1'], env)
        if self.check_if_returns_raised_error(eval1):
            return eval1
        eval2 = self.evaluate_expression(expression_node.dict['op2'], env)
        if self.check_if_returns_raised_error(eval2):
            return eval2
        if (type(eval1) is not bool) or (type(eval2) is not bool):
            super().error(ErrorType.TYPE_ERROR, f"Comparison args for {expression_node.elem_type} must be of same type bool.",)
        # forces evaluation on both (strict evaluation)
        eval1 = bool(eval1)
        eval2 = bool(eval2)
        match expression_node.elem_type:
            case '&&':
                return (eval1 and eval2)
            case '||':
                return (eval1 or eval2)
    # No more functions remain... for now... :)

#DEBUGGING
# program = """
# func main() {
#   var vd;
#   vd = false;
#   if (inputs() == "I'm in") {
#     var i;
#     for (i = 0; i < 10; i = i + 1) {
#       var x;
#       x = i * i - 7 * i + 10 > 0;
#       if (x) {
#         vd = x;
#         print("above zero");
#       } else {
#         print("below zero");
#       }
#       var i;
#       i = x;
#     }
#     print(i);
#     print(x);
#   }
# }
#  """
# interpreter = Interpreter()
# interpreter.run(program)
No known bugs! All good!

Nov 23 - Added Lazy evaluation - Unsure if actually correct, tried 12-13 testcases and they were correct
            - Implemented via Thunk class as suggested in https://www.cs.virginia.edu/~evans/cs150/book/ch13-laziness-0402.pdf
            - Passed env (variable scope) throughout interpreter
            - Lot of change in one commit since I had to manually add ', env' argument in every run_statement and evaluate_expression call
        - Still need exception handling and short circuiting, as well as more extensive testing with lazy eval once implemented.
        - 
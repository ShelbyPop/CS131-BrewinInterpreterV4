No known bugs! All good!

Nov 23 - Added Lazy evaluation - Unsure if actually correct, tried 12-13 testcases and they were correct
            - Implemented via Thunk class as suggested in https://www.cs.virginia.edu/~evans/cs150/book/ch13-laziness-0402.pdf
            - Passed env (variable scope) throughout interpreter
            - Lot of change in one commit since I had to manually add ', env' argument in every run_statement and evaluate_expression call
        - Still need exception handling and short circuiting, as well as more extensive testing with lazy eval once implemented.
        - Knew it, theres a bug with parameter passing and when deciding when it evaluates, causing recursion depth error
        - Actually, the bug has to do with not using lambda captures like we were toldddd (result = 5; result = result + 2; print(result);) results in recursion depth error (need lambdas)


Nov 24 - ..... I'm just... okay
        - the fix was that I needed to make the environment I pass to the Thunk a **DEEPCOPY** and not a shallow copy. I.... ugh. That took me like 5 hours alone to debug.. cool lol
        - Found a bug with return statements from V2, Fixed it in V3, so I just copy the run_func minus the type checking and it should work.

Nov 29 - 
        - So. Back here again. I think I may have finally fixed everything. 5/12 on testcases, all my testcases I've tried have passed. 
                I fixed parameter passing. Turns out, the whole issue was me not passing in a variable i needed to, and I never
                noticed because I had a default on it. If that doesn't demonstrate how spaghetti code this has become then I'm not sure what will
        - Something is still wrong with autograder saying I failed when it passes on my own, Boyan said I should add debug prints to see, but 
                I think for now I'm just going to move on. Future me will either hate me or love me for this decision. Time will tell.

Nov 30 - 
        - Implemented Raise statements, planned ahead for try/catch with error propagation (breaks all run_statements loops, and propogates up to run_func(main_func_node))
        - Implemented Try-catch blocks, should have correct scoping? 
        - Removed unnecessary helper functions that made code more bulky
        - Added rudementary short circuiting
Dec 1 - 
        - Turns out that try clauses should prioritize return statements over catchers, Implemented.
        
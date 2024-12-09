from traceback import extract_stack

def print_last_function_call():
    #get the call stack
    stack = extract_stack()
    print(stack)

print("test")
print_last_function_call()
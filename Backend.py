#Testing
 #!/usr/bin/env python3
"""
basic_script.py
A tiny Python demo: greeting, simple calculator, factorial, Fibonacci, and file IO.
"""

def greet(name: str) -> None:
    print(f"Hello, {name}! 👋")

def add(a: float, b: float) -> float:
    return a + b

def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def fibonacci(n: int) -> list[int]:
    if n <= 0:
        return []
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq[:n]

def demo_file_io(filename: str) -> None:
    # write a short message, then read it back
    with open(filename, "w") as f:
        f.write("This is a small file created by basic_script.py\n")
    with open(filename, "r") as f:
        content = f.read()
    print("File contents:")
    print(content.strip())

def main():
    # Greeting
    greet("friend")

    # Simple calculator
    x, y = 3.5, 2.2
    print(f"{x} + {y} = {add(x, y)}")

    # Factorial
    n = 5
    print(f"{n}! = {factorial(n)}")

    # Fibonacci
    print("First 7 Fibonacci numbers:", fibonacci(7))

    # File I/O demo
    demo_file_io("example.txt")

if __name__ == "__main__":
    main()

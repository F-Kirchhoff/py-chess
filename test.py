import itertools


for piece in itertools.product(("b", "w"), ("k", "q", "r","n","b","p")):
    print("".join(piece))

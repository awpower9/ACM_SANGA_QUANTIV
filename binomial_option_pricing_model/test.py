try:
    import binomial_engine
    engine = binomial_engine.BinomialEngine()
    USE_CPP = True
    print("✓ Using C++ binomial engine")
except ImportError:
    USE_CPP = False
    print("⚠ C++ engine not available, using Python fallback")


S = 100
K = 100
t = 1
v = 0.2
N = 100
result = engine.calculate_option(S,K,t,0.05,v,True,N)

print(result.price)
print(result.delta)
print(result.gamma)
print(result.theta)
print(result.vega)
print(result.rho)
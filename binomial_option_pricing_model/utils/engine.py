import numpy as np
import scipy.stats as si

try:
    import quantiv_engine as qe
    C_ENGINE = qe
    ENGINE_TYPE = "quantiv_engine"
    HAS_CPP = True
except ImportError:
    try:
        import binomial_engine as qe
        C_ENGINE = qe
        ENGINE_TYPE = "binomial_engine"
        HAS_CPP = True
    except ImportError:
        C_ENGINE = None
        ENGINE_TYPE = None
        HAS_CPP = False

class PythonEngine:
    """Fallback Python implementation of pricing models matching C++ signatures."""
    
    @staticmethod
    def calculate(S, K, T, sigma, is_call):
        # Mirroring C++ BlackScholes::calculate which uses 5 args (r=0.05 default)
        r = 0.05
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if is_call:
            price = S * si.norm.cdf(d1) - K * np.exp(-r * T) * si.norm.cdf(d2)
            delta = si.norm.cdf(d1)
        else:
            price = K * np.exp(-r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)
            delta = si.norm.cdf(d1) - 1
            
        return type('BSMResult', (), {
            'price': price, 'delta': delta, 'gamma': 0.0, 
            'theta': 0.0, 'vega': 0.0, 'rho': 0.0
        })

    @staticmethod
    def calculate_option(S, K, T, r, sigma, is_call, steps, american=True):
        # Mirroring C++ BinomialEngine::calculate_option
        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp(r * dt) - d) / (u - d)
        disc = np.exp(-r * dt)
        
        prices = np.zeros(steps + 1)
        for i in range(steps + 1):
            prices[i] = S * (u**(steps - i)) * (d**i)
            
        values = np.maximum(prices - K if is_call else K - prices, 0)
        
        for j in range(steps - 1, -1, -1):
            for i in range(j + 1):
                values[i] = disc * (p * values[i] + (1 - p) * values[i + 1])
                if american:
                    st = S * (u**(j - i)) * (d**i)
                    exercise = max(st - K if is_call else K - st, 0)
                    values[i] = max(values[i], exercise)
                    
        return type('OptionResult', (), {
            'price': values[0], 'delta': 0.0, 'gamma': 0.0, 
            'theta': 0.0, 'vega': 0.0, 'rho': 0.0, 'steps': steps
        })

    def bsm_calculate(self, S, K, T, sigma, r, is_call):
        return self.calculate(S, K, T, sigma, is_call)

    def get_tree_structure(self, *args, **kwargs):
        return []

    def calculate_vol_surface(self, S, r, is_call, steps, strikes, maturities, vols, american):
        # Realistic fallback surface
        results = []
        for mat in maturities:
            row = []
            for strike in strikes:
                res = self.calculate_option(S, strike, mat, r, 0.2, is_call, 10, american)
                row.append(res.price)
            results.append(row)
        return results

    @staticmethod
    def calculate_merton(S, K, T, r, sigma, lam, mu, delta, is_call):
        # Python Fallback for Merton Jump Diffusion
        import math
        k = math.exp(mu + 0.5 * delta**2) - 1
        lambda_p = lam * (1 + k)
        p = 0.0
        for n in range(15):
            fact = math.factorial(n)
            weight = (math.exp(-lambda_p * T) * (lambda_p * T)**n) / fact
            sigma_n = math.sqrt(sigma**2 + (n * delta**2) / T)
            r_n = r - lam * k + (n * math.log(1 + k)) / T
            d1 = (math.log(S/K) + (r_n + 0.5 * sigma_n**2) * T) / (sigma_n * math.sqrt(T))
            d2 = d1 - sigma_n * math.sqrt(T)
            def N(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
            bs = (S * N(d1) - K * math.exp(-r_n * T) * N(d2)) if is_call else (K * math.exp(-r_n * T) * N(-d2) - S * N(-d1))
            p += weight * bs
        
        return type('MJResult', (), {'price': p, 'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0})

    @staticmethod
    def calculate_heston(S, K, T, r, kappa, theta, xi, rho, is_call):
        # Simplified Heston Fallback (using BSM as placeholder if full Fourier transform is too heavy)
        # For full accuracy, a numerical integration is needed. 
        # Here we map Heston long-term vol to BSM vol for a rough estimate
        vol = math.sqrt(theta)
        return PythonEngine.calculate(S, K, T, vol, is_call)

    # Aliases
    def calculate_mjd(self, *args, **kwargs): return self.calculate_merton(*args, **kwargs)


def get_binomial_engine():
    if HAS_CPP and hasattr(C_ENGINE, 'BinomialEngine'):
        return C_ENGINE.BinomialEngine()
    return PythonEngine()

def get_bsm_engine():
    if HAS_CPP and hasattr(C_ENGINE, 'BlackScholes'):
        return C_ENGINE.BlackScholes()
    return PythonEngine()

def get_merton_engine():
    if HAS_CPP and hasattr(C_ENGINE, 'Merton'):
        return C_ENGINE.Merton()
    return PythonEngine()

def get_heston_engine():
    if HAS_CPP and hasattr(C_ENGINE, 'Heston'):
        return C_ENGINE.Heston()
    return PythonEngine()

def get_engine_status():
    return {
        "has_cpp": HAS_CPP,
        "engine_type": ENGINE_TYPE,
        "backend": "C++ (High Performance)" if HAS_CPP else "Python (Standard)"
    }

#pragma once
#include<cmath>
#include<algorithm>

struct BSMResult{
     double price;
     double delta;
     double gamma;
     double theta;
     double vega;
     double rho;
};

class BlackScholes{
      double normalCDF(double x) const;
      double normalPDF(double x) const;

    public:
      
      BlackScholes()=default;

      BSMResult calculate(double S,double K,double t,double v,bool is_call);

};
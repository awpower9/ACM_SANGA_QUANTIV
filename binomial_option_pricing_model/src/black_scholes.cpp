#include "../include/black_scholes.h"
#include <iostream>
using namespace std;

double BlackScholes::normalCDF(double x) const{
    return 0.5*(1.0+erf(x/sqrt(2.0)));
}

double BlackScholes::normalPDF(double x) const{
    static const double invert_2pi=0.3989422804014327;
    return invert_2pi*exp(-0.5*x*x);
}

BSMResult BlackScholes::calculate(double S,double K,double t,double v,bool is_call){
    BSMResult res={0.0,0.0,0.0,0.0,0.0,0.0};

    double r=0.05;

    if(S<=0 || K<=0 || t<=0 || v<=0 )return res;

    if(t==0){
        res.price=is_call?max(S-K,0.0): max(K-S,0.0);
        res.delta=is_call?(S>K?1.0:0.0):(S<K?-1.0:0.0);
        return res;
    }

    double sqrtT=sqrt(t);
    double d1=(log(S/K)+(r*0.5*v*v)*t)/(v*sqrtT);
    double d2=d1-v*sqrtT;

    double Nd1=normalCDF(d1);
    double Nd2=normalCDF(d2);
    double N_d1=normalCDF(d1);
    double N_d2=normalCDF(d2);
    double pdf_d1=normalPDF(d1);

    //Option price
    if(is_call){
        res.price=S*Nd1-K*exp(-r*t)*Nd2;

    }else{
        res.price=K*exp(-r*t)*N_d2-S*N_d1;
    }

    //delta
    res.delta=is_call?Nd1:Nd1-1;

    //gamma
    res.gamma=pdf_d1/(S*v*sqrtT);

    //Vega
    res.vega=(S*sqrtT*pdf_d1)/100.0;

    //theta
    double term1=-(S*pdf_d1*v)/(2.0*sqrtT);
    res.theta=is_call?(term1-r*K*exp(-r*t)*Nd2):(term1+r*K*exp(-r*t)*N_d2);
    res.theta/=365.0;

    //rho
    if(is_call){
        res.rho=(K*t*exp(-r*t)*Nd2)/100.0;
    }else{
        res.rho=(-K*t*exp(-r*t)*N_d2)/100.0;
    }

    return res;
}
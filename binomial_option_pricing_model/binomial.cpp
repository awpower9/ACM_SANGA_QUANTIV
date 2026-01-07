#include <iostream>
#include <bits/stdc++.h>
using namespace std;
class binomialOptionPricingModel{
    public:
        binomialOptionPricingModel(int T,int n, int volatility,int type,int currentPrice,int strikePrice,int riskFreeRate){
            double delta_t=((double)T/n);
            double u=exp(volatility*sqrt(delta_t));
            double d=exp(volatility*sqrt(delta_t)*(-1));
            double riskFreeGrowthRate=exp(riskFreeRate*delta_t);
            double discountFactor=exp(riskFreeRate*delta_t*(-1));
            double upProbability=(riskFreeGrowthRate-d)/(u-d);
            double downProbability=1-upProbability;
            vector<vector<double>> optionPriceGrid(1000,vector<double>(100));
            for(int i=0;i<n;i++){
                for(int j=0;j<=i;j++){
                    optionPriceGrid[i][j]=(currentPrice)*(pow(u,j))*(pow(d,i-j)); 
                }
            }
            for (int j = 0; j <= n; j++) {
                double stockPrice = currentPrice * pow(u, j) * pow(d, n - j);
                if (type)
                    optionPriceGrid[n][j] = max(stockPrice - strikePrice, 0.0);
                else
                    optionPriceGrid[n][j] = max(strikePrice - stockPrice, 0.0);
            }

            for(int i=n-1;i>=0;i--){
                for(int j=0;j<=i;j++){
                    optionPriceGrid[i][j]=discountFactor*(upProbability*(optionPriceGrid[i+1][j+1])+downProbability*(optionPriceGrid[i+1][j]));
                }
            }
            
        }
};
int main(){

}
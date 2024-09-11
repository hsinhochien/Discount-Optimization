# Discount-Optimization
Prerequisite: <br>
```pip install pulp==2.9.0``` <br>

This repository provides a solution for optimizing discounts based on a given set of products, discount types, and various constraints. The solution is implemented using the PuLP library, a Python tool for linear programming. <br>

Explanation: 
1. Variable Definition:
> * ```x[i, d]```: Whether discount ```d``` is applied to product set ```i```.
> * ```z[i]```: Whether product set ```i``` is selected.
> * ```y[i]```: Whether the discount ```d``` threshold is met.
2. Constraints:
> * Each product set can use at most one discount.
> * Discounts are applied only when the threshold (price or quantity) is met.
> * Discounts are subject to usage limits.
3. Objective Function:
The function maximizes the total discount based on the discount rates and product prices.
> Using the Global Weather Repository CSV, perform the following analysis:
> 1. **Prepare the data** for modeling (handle any quality issues you find)
> 2. **Build two predictive models** for `temperature_celsius`:
>    - One **tree-based model** (e.g., Random Forest or Gradient Boosting)
>    - One **linear model** (e.g., Linear Regression or Ridge Regression)
> 3. **Print model results to the console** after training:
>    - For each model: R², MAE, and RMSE on the test set
>    - The list of features used (names and count)
>    - The train/test split ratio used
>    - Top 5 most important features (by importance or absolute coefficient)
> 4. Produce exactly **4 visualizations**:
>    - Feature importance/coefficients comparison between the two models
>    - Actual vs. predicted scatter plot for the tree-based model
>    - Actual vs. predicted scatter plot for the linear model
>    - One additional visualization of your choice that supports a key finding
> 5. Write a **400-word analytical report** comparing the models: explain why they differ in performance, which features matter most, and recommend which model to deploy
> Note: In code and chart labels, use ASCII 'deg C' or 'Celsius' (do not use the degree symbol ° to avoid encoding errors).
> Column reference: cities are in `location_name`, countries in `country`, temperature in `temperature_celsius`, timestamps in `last_updated`.
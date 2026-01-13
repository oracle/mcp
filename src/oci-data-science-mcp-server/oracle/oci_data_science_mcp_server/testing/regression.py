from sklearn.datasets import make_regression
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import numpy as np
import sklearn.metrics as metrics

# 1. Create a dummy regression dataset
# We generate 100 samples with 5 features
X, y = make_regression(n_samples=1000, n_features=20, noise=15, random_state=42)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

# 2. Define the pipeline with StandardScaler and LinearRegression
# The steps are defined as (name, transformer/estimator) tuples
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', LinearRegression())
])

# 3. Fit the model on the transformed data
# The pipeline handles the scaling and fitting automatically
pipeline.fit(X_train, y_train)

# Let's see some results
print("Pipeline steps:")
print(pipeline.steps)
print("-" * 20)

# We can also get the fitted model and scaler from the pipeline
# The 'named_steps' attribute gives us access to the individual components
fitted_scaler = pipeline.named_steps['scaler']
fitted_model = pipeline.named_steps['regressor']

# You can now use the fitted pipeline to make predictions

prediction = pipeline.predict(X_test)


def regression_results(y_true, y_pred):
    # Regression metrics
    explained_variance=metrics.explained_variance_score(y_true, y_pred)
    mean_absolute_error=metrics.mean_absolute_error(y_true, y_pred) 
    mse=metrics.mean_squared_error(y_true, y_pred) 
    median_absolute_error=metrics.median_absolute_error(y_true, y_pred)
    r2=metrics.r2_score(y_true, y_pred)

    print('explained_variance: ', round(explained_variance,4))    
    print('r2: ', round(r2,4))
    print('MAE: ', round(mean_absolute_error,4))
    print('MSE: ', round(mse,4))
    print('RMSE: ', round(np.sqrt(mse),4))

regression_results(y_test,prediction)
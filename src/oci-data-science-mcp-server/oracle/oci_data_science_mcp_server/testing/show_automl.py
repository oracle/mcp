import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from automl import AutoClassifier  # Assuming Oracle AutoMLX is imported this way

# Load sample dataset for binary classification
data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = data.target

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize AutoMLX for classification
automl = AutoClassifier(
    n_jobs=-1,  # Use all available cores
    cv=5,       # 5-fold cross-validation
    verbose=2   # Verbosity level
)

# Fit the model
automl.fit(X_train, y_train)

# Make predictions
predictions = automl.predict(X_test)

# Print model details
print("Best model:", automl.best_estimator_)
print("Best score:", automl.best_score_)

# Evaluate on test set
from sklearn.metrics import accuracy_score
accuracy = accuracy_score(y_test, predictions)
print("Test accuracy:", accuracy)

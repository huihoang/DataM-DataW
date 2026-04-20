import joblib

# ===== LOAD MODELS =====
PATH_MODELS = "artifacts/modeling_results/trained_models/"
models = {
    "Logistic Regression": PATH_MODELS + "imbalanced__LogisticRegression.pkl",
    "Decision Tree": PATH_MODELS + "imbalanced__DecisionTree.pkl",
    "Naive Bayes": PATH_MODELS + "imbalanced__Bayesian_GaussianNB.pkl",
    "ANN (MLP)": PATH_MODELS + "imbalanced__ANN_MLP.pkl"
}

def inspect_model(name, model):
    print("=" * 50)
    print(f"MODEL: {name}")
    print("=" * 50)

    # ===== BASIC INFO =====
    print("\n[Basic Info]")
    print(model)

    # ===== PARAMETERS =====
    if hasattr(model, "get_params"):
        print("\n[Parameters]")
        for k, v in model.get_params().items():
            print(f"{k}: {v}")

    # ===== COMMON ATTRIBUTES =====
    print("\n[Common Attributes]")
    if hasattr(model, "classes_"):
        print("classes_:", model.classes_)
    if hasattr(model, "n_features_in_"):
        print("n_features_in_:", model.n_features_in_)

    # ===== MODEL-SPECIFIC =====
    print("\n[Model Specific Info]")

    # Logistic Regression
    if hasattr(model, "coef_"):
        print("coef_:", model.coef_)
        print("intercept_:", model.intercept_)

    # Decision Tree
    if hasattr(model, "tree_"):
        print("tree depth:", model.get_depth())
        print("n_leaves:", model.get_n_leaves())

    # Naive Bayes
    if hasattr(model, "class_prior_"):
        print("class_prior_:", model.class_prior_)
    if hasattr(model, "theta_"):
        print("mean (theta_):", model.theta_)
    if hasattr(model, "var_"):
        print("variance (var_):", model.var_)

    # ANN (MLP)
    if hasattr(model, "coefs_"):
        print("Number of layers:", len(model.coefs_))
        for i, w in enumerate(model.coefs_):
            print(f"Layer {i} weights shape:", w.shape)

    print("\n")


# ===== MAIN =====
if __name__ == "__main__":
    for name, path in models.items():
        try:
            model = joblib.load(path)
            inspect_model(name, model)
        except Exception as e:
            print(f"Failed to load {name}: {e}")
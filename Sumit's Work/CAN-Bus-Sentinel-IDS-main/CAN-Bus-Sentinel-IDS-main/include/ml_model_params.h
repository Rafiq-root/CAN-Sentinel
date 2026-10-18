// Auto-generated ML model parameters
// DO NOT EDIT MANUALLY

#ifndef ML_MODEL_PARAMS_H
#define ML_MODEL_PARAMS_H

// Feature scaling parameters (StandardScaler)
#define ML_NUM_FEATURES 6

static const float ML_FEATURE_MEANS[ML_NUM_FEATURES] = {
    428.947977f, 2.872832f, 22.874277f, 49652801.225434f, 11.352601f, 72.323699f
};

static const float ML_FEATURE_STDS[ML_NUM_FEATURES] = {
    240.866890f, 1.452927f, 18.712817f, 459120628.360337f, 6.631285f, 78.896137f
};

// Isolation Forest threshold
#define ML_THRESHOLD -0.8f    //so it can catch most anomalies

#endif // ML_MODEL_PARAMS_H

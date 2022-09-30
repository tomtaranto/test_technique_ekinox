import matplotlib.pyplot as plt
import pandas as pd
import tensorflow as tf
from keras import layers
from sklearn.model_selection import train_test_split
from tensorflow import feature_column
from terminaltables import AsciiTable

# Transforme un df en dataset tensorflow
def df_to_dataset(dataframe, shuffle=True, batch_size=32):
    dataframe = dataframe.copy()
    labels = dataframe.pop('FinalGrade')
    ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(dataframe))
    ds = ds.batch(batch_size)
    return ds


# Cree un model simple et split le dataset en train,val, test
def create_model(dataframe):
    feature_columns = []

    # Categorical columns
    categorical_col_names = ['school', 'sex', 'age', 'address', 'famsize', 'Pstatus', 'Medu', 'Fedu', 'Mjob', 'Fjob',
                             'reason', 'guardian', 'traveltime', 'studytime', 'schoolsup', 'famsup', 'paid',
                             'activities', 'nursery', 'higher', 'internet', 'romantic', ]
    for col_name in categorical_col_names:
        categorical_column = feature_column.categorical_column_with_vocabulary_list(
            col_name, dataframe[col_name].unique())
        indicator_column = feature_column.indicator_column(categorical_column)
        feature_columns.append(indicator_column)

    # Numeric cols
    for header in dataframe.columns:
        if (header not in categorical_col_names) and (header != "FinalGrade"):
            feature_columns.append(feature_column.numeric_column(header))

    feature_layer = tf.keras.layers.DenseFeatures(feature_columns)
    train, test = train_test_split(dataframe, test_size=0.2)
    train, val = train_test_split(train, test_size=0.2)

    model = tf.keras.Sequential([
        feature_layer,
        layers.Dense(128, activation='relu'),
        layers.Dense(128, activation='relu'),
        layers.Dropout(.1),
        layers.Dense(1)
    ])
    return model, train, test, val


# Entraine sur un data frame
def train(dataframe):
    dataframe.drop(columns=["StudentID", "FirstName", "FamilyName"], inplace=True)
    model, train, test, val = create_model(dataframe)
    batch_size = 20
    train_ds = df_to_dataset(train, batch_size=batch_size)
    val_ds = df_to_dataset(val, shuffle=False, batch_size=batch_size)
    test_ds = df_to_dataset(test, shuffle=False, batch_size=batch_size)

    model.compile(optimizer='adam',
                  loss=tf.keras.losses.MSE)

    history = model.fit(train_ds,
                        validation_data=val_ds,
                        epochs=10)

    return history.history, model,


# Permet de visualiser les courbes d'entrainement
def plot_convergence(history):
    for k in history.keys():
        plt.plot(history[k], label=k)
    plt.legend()
    plt.show()


# Fonction d'inference
def infer(df, model):
    ds = df_to_dataset(df, shuffle=False, batch_size=1)
    all_diff, all_score = [], []
    for feature, label in ds:
        score = float(model(feature))
        diff = abs(float(label) - score)
        all_diff.append(diff)
        all_score.append(score)
    df = pd.read_csv("data/student_data.csv")
    df['prediction'] = all_score
    df['diff'] = all_diff
    df.sort_values(by='diff', inplace=True, ascending=False)
    to_check = (abs(df['diff']) > 4) & (df['FinalGrade'] < 10)
    students = df[to_check]
    table = [["Nom", "Prenom", "Difference"]]
    for (first, family, improve) in zip(students['FamilyName'], students['FirstName'], students['diff']):
        table += [[first, family, improve]]
    print(AsciiTable(table).table)
    plt.hist(all_diff)
    plt.show()


def main():
    df = pd.read_csv("data/student_data.csv")
    h, model = train(df)
    plot_convergence(h)
    infer(df, model)


if __name__ == '__main__':
    main()

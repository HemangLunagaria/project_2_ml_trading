from inspect import isgenerator
import pandas as pd
import datetime as dt 

df_data = pd.read_csv('Resources/Training_data.csv', index_col=0, infer_datetime_format=True)
df_data.index.set_names('Date', inplace=True)

df_data['Target_returns'] = df_data.Returns.shift(-1)
df_data.dropna(inplace=True)
df_data['Buy_or_sell'] = df_data.Target_returns.apply(lambda x: 'Buy' if x > 0 else 'Dont_buy')

curr_list = [ 'ETH/AUD', 'XRP/AUD', 'LTC/AUD', 'ADA/AUD', 'XLM/AUD', 'BCH/AUD' ]         # 'ETH/AUD', 'XRP/AUD', 'LTC/AUD', 'ADA/AUD', 'XLM/AUD', 'BCH/AUD'
test_currs = ['ETH/AUD', 'XRP/AUD', 'LTC/AUD', 'ADA/AUD', 'XLM/AUD', 'BCH/AUD']
indicators_list = ['BBands_high', 'BBands_low', 'RSI_ratio', 'CCI','ADX', 'ADX_dirn'] #, 'MACD_ratio', 'ATR_ratio', 'SMA_agg', 
# model_for_testing = 'grad_boost'
all_models = [ 'svc', 'dec_tree', 'forest' , 'ada_boost' ]        #,'svc', 'dec_tree', 'forest', 'grad_boost', 'ada_boost'



for model_for_testing in all_models:

    current_index = 0
    # num_records = len(df_filtered)
    df_filtered = df_data.loc[ df_data.Currency.isin(curr_list) ]


    X = df_filtered.loc[:,indicators_list].reset_index(drop=True)        
    y = df_filtered.Buy_or_sell

    num_of_training_recs = X.shape[0]

    from imblearn.over_sampling import SMOTE
    from imblearn.combine import SMOTEENN

    # resampler = SMOTE(random_state= 1)
    combi_sampler = SMOTEENN(random_state=42)
    X , y = combi_sampler.fit_resample(X , y)
    y.value_counts()

    from sklearn.tree import DecisionTreeClassifier
    from sklearn.svm import SVC
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
    # import xgboost as xgb 

    svc = SVC()
    dec_tree = DecisionTreeClassifier()
    logreg = LogisticRegression( solver='liblinear')
    forest = RandomForestClassifier( criterion='gini')
    grad_boost = GradientBoostingClassifier()
    ada_boost = AdaBoostClassifier()

    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.compose import ColumnTransformer, make_column_transformer
    from sklearn.decomposition import PCA

    col_transform = make_column_transformer(
        (StandardScaler(), X.columns.to_list())
    )
    col_transform.fit_transform(X);

    pca = PCA(n_components=3)

    # chain sequential steps together
    from sklearn.pipeline import make_pipeline, Pipeline

    if model_for_testing == 'svc': model = ('svc', svc)
    elif model_for_testing == 'logreg': model = ('logreg', logreg)
    elif model_for_testing == 'dec_tree': model = ('dec_tree', dec_tree)
    elif model_for_testing == 'forest': model = ('forest', forest)
    elif model_for_testing == 'grad_boost': model = ('grad_boost', grad_boost)
    elif model_for_testing == 'ada_boost': model = ('ada_boost', ada_boost)

    pipe = Pipeline(steps= [('col_transform', col_transform), 
                        ('pca', pca),
                        model
                        ])

    cross_val_roc_auc = cross_val_score(pipe, X, y, cv=10, scoring='roc_auc', n_jobs=20).mean()

    cross_val_accuracy = cross_val_score(pipe, X, y, cv=10, scoring='accuracy', n_jobs=20).mean()

    from sklearn.model_selection import GridSearchCV
    params = {}

    if model_for_testing == 'logreg':
        params['logreg__solver'] = ['liblinear', 'lbfgs']
        params['logreg__C'] = [0.5, 0.75, 1, 1.25, 1.5]
        params['logreg__penalty'] = ['l1', 'l2']


    elif model_for_testing == 'svc': 
        params['svc__C'] = [0.5, 0.75, 1, 1.25, 1.5]
        params['svc__kernel'] = ['linear', 'poly', 'rbf', 'sigmoid', 'precomputed']

    elif model_for_testing == 'dec_tree': 
        params['dec_tree__criterion'] = ['gini', 'entropy']
        params['dec_tree__max_depth'] = list(range(3,8,1))


    elif model_for_testing == 'forest':
        params['forest__n_estimators'] = list(range(100,150,10))
        params['forest__max_depth'] = list(range(3,8,1))
        params['forest__max_features'] = ['auto', 'sqrt', 'log2']


    elif model_for_testing == 'grad_boost': 
        params['grad_boost__learning_rate'] = [0.075, 0.1, 0.25, 0.5]
        params['grad_boost__n_estimators'] = list(range(100,200,10))
        params['grad_boost__max_features'] = ['auto', 'sqrt', 'log2']
        params['grad_boost__max_depth'] = list(range(3,8,1))
        params['grad_boost__loss'] = ['deviance', 'exponential']


    elif model_for_testing == 'ada_boost': 
        params['ada_boost__n_estimators'] = list(range(100,200,10))
        params['ada_boost__learning_rate'] = [0.05, 0.075, 0.1]
        params['ada_boost__algorithm'] = ['SAMME.R']

    grid = GridSearchCV(pipe, params, cv=10, scoring='roc_auc', n_jobs=20)
    grid.fit(X,y)

    estimator = grid.best_estimator_[model_for_testing]
    grid_best_params = str(grid.best_params_)
    grid_best_params
    gridcv_best_score = grid.best_score_

    pipeline = make_pipeline(
        col_transform, 
        pca, 
        estimator)
    pipeline.fit(X, y)

    df_testing_data = pd.read_csv('Resources/Testing_data.csv', index_col=0, infer_datetime_format=True)
    df_testing_data.index.set_names('Date', inplace=True)

    # df_testing_data.head(2)
    df_testing_data['Target_returns'] = df_testing_data.Returns.shift(-1)
    df_testing_data.dropna(inplace=True)
    df_testing_data['Buy_or_sell'] = df_testing_data.Target_returns.apply(lambda x: 'Buy' if x > 0 else 'Dont_buy')

    df_testing_subset = df_testing_data.loc[ df_testing_data.Currency.isin(test_currs) ] 
    X_test = df_testing_subset.loc[: , indicators_list].reset_index(drop=True)   
    y_test = df_testing_subset.loc[:, ['Target_returns', 'Buy_or_sell']].copy()

    df_pred = y_test
    df_pred['Pred_buy_or_sell'] = pipeline.predict(X_test)

    from sklearn.metrics import classification_report
    from imblearn.metrics import classification_report_imbalanced

    y_pred = pipeline.predict(X_test)
    # print(y_pred)
    df_predictions = pd.DataFrame(y_pred, columns=['Buy'])
    
    class_report = classification_report(y_test.Buy_or_sell, y_pred, output_dict=True)
    test_accuracy = class_report['accuracy']

    total_returns_pred_buy = df_pred.loc[df_pred.Pred_buy_or_sell == 'Buy'].copy()
    total_pnl = total_returns_pred_buy.Target_returns.sum()

    # Writing the outcomes to csv 
    currency = ' '.join(curr_list)
    indicators = ','.join(indicators_list)
    model_tested = model[0]

    df_outcomes = pd.read_csv('Resources/GridSearch_loop.csv', index_col=0)
    # df_outcomes = pd.DataFrame(columns=['Num_recs', 'currency', 'Indicators', 'Model_tested', 'CV_ROC', 'CV_Accuracy', 'Grid_best_score', 'grid_best_params', 'Test_accuracy', 'Total_pnl'], index = None)

    df_outcomes = df_outcomes.append(pd.Series([ 
        currency,
        indicators,
        model_tested,
        cross_val_roc_auc,
        cross_val_accuracy,
        gridcv_best_score, 
        grid_best_params,
        test_accuracy,
        total_pnl
    ],index = df_outcomes.columns), ignore_index=True)

    df_outcomes.to_csv('Resources/GridSearch_loop.csv')

    print(f'Updated the csv for {model_for_testing}')


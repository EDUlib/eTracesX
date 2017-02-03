import sql_functions

def record_experiment(db_name, username, passwd, host, port, lead, lag, auc_train,
        testing_course, auc_test, p_lambda, p_epsilon, exp_time_stamp):
    conn = sql_functions.openSQLConnectionP(db_name, username, passwd, host, port)
    ##returns exp_id
    sql = '''INSERT INTO `%s`.`experiments`
          (`lead`,
          `lag`,
          `auc_train`,
          `course_test_id`,
          `auc_test`,
          `parameter_lambda`,
          `parameter_epsilon`,
          `experiment_time_stamp`
          )
        VALUES (%s, %s, %s, '%s', %s, %s, %s, '%s')''' % (db_name, lead, lag,
        auc_train, testing_course, auc_test, p_lambda, p_epsilon,
        exp_time_stamp)

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.commit()

    sql = "SELECT exp_id FROM `%s`.`experiments` WHERE experiment_time_stamp = '%s'" % (db_name, exp_time_stamp)
    cursor = conn.cursor()
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return int(max(data, key=lambda x: int(x[0]))[0])

def record_model(db_name, username, passwd, host, port, features, model, exp_id):
    #model = [f1_w1_value,
    #         f2_w1_value
    #         f3_w1_value
    #         f1_w2_value,
    #         f2_w2_value,
    #         f3_w2_value,
    #         ...]
    conn = sql_functions.openSQLConnectionP(db_name, username, passwd, host, port)
    sql = "INSERT INTO %s.models(longitudinal_feature_id," % db_name
    sql = sql+ '''
        longitudinal_feature_week,
        longitudinal_feature_value,
        exp_id)
        VALUES (%s, %s, %s, %s)
        '''
    data = [(features[0], 0, model[0][0], exp_id)]
    week = 0
    num_features= len(features)-1
    for i,value in enumerate(model[1:]):
        feature_idx = (i % num_features)+1
        if feature_idx == 0 and i != 0:
            week += 1
        data.append((features[feature_idx], week, value[0], exp_id))

    cursor = conn.cursor()
    cursor.executemany(sql,data)
    cursor.close()
    conn.commit()
    conn.close()

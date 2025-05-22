import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import joblib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import itertools
import numpy as np
import random


DATA_DIR = Path('../regions_fire')
MODELS_DIR = Path('models')
PLOTS_DIR = Path('plots')

MODELS_DIR.mkdir(exist_ok=True)
PLOTS_DIR.mkdir(exist_ok=True)

def train_for_region(region_id, num_samples=8, transform_log=False):
    data_path = DATA_DIR / f'{region_id}.json'
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Файл {data_path} не найден")
        return

    full_range = pd.date_range('2012-03-01', '2021-09-30', freq='ME')

    param_grid = {
        'changepoint_prior_scale': [0.01, 0.1, 0.5, 2.0],
        'seasonality_prior_scale': [5.0, 15.0, 25.0],
        'seasonality_mode': ['additive', 'multiplicative'],
        'interval_width': [0.80]
    }
    all_params = [
        dict(zip(param_grid.keys(), vals))
        for vals in itertools.product(*param_grid.values())
    ]

    for use_anomaly in [False, True]:
        suffix = f"{region_id}_{'anomaly' if use_anomaly else 'no_anomaly'}"
        models, metrics = {}, {}

        sampled = random.sample(all_params, k=min(num_samples, len(all_params)))

        for fire_type, dates in data['fires'].items():
            if data['fire_stats'].get(fire_type, 0) < 80:
                continue

            df = pd.DataFrame({'ds': pd.to_datetime(dates), 'y': 1})
            df = (
                df.groupby(pd.Grouper(key='ds', freq='ME')).sum()
                  .reindex(full_range, fill_value=0)
                  .reset_index().rename(columns={'index':'ds'})
            )
            if df['y'].sum() == 0:
                continue

            if transform_log:
                df['y'] = np.log1p(df['y'])

            if use_anomaly:
                df['anomaly'] = df['ds'].apply(
                    lambda x: 1 if pd.Timestamp('2020-01-01') <= x <= pd.Timestamp('2021-09-30')
                    else 0
                )

            best_mae, best_model, best_params = float('inf'), None, None

            for params in sampled:
                try:
                    m = Prophet(
                        yearly_seasonality=False,
                        weekly_seasonality=False,
                        n_changepoints=6,                
                        changepoint_prior_scale=params['changepoint_prior_scale'], 
                        seasonality_mode=params['seasonality_mode'],
                        interval_width=params['interval_width']
                    )
                    m.add_seasonality(
                        name='yearly',
                        period=365.25,
                        fourier_order=4,
                        prior_scale=params['seasonality_prior_scale']
                    )
                    if use_anomaly:
                        m.add_regressor('anomaly', prior_scale=1.0, mode='additive')

                    m.fit(df)
                    df_cv = cross_validation(
                        m,
                        initial='730 days',
                        period='180 days',
                        horizon='365 days',
                        parallel='processes'
                    )
                    perf = performance_metrics(df_cv)
                    mae = perf['mae'].mean()
                    if mae < best_mae:
                        best_mae, best_model, best_params = mae, m, params
                except Exception:
                    continue

            if best_model:
                models[fire_type] = best_model
                metrics[fire_type] = {'mae': best_mae, 'params': best_params}
                print(f"{suffix}: {fire_type} → MAE={best_mae:.5f}, params={best_params}")

        if models:
            joblib.dump({'models': models, 'metrics': metrics},
                        MODELS_DIR / f"{suffix}.pkl")

    return


def show_metrics(suffix, transform_log):
    pkl_path = MODELS_DIR / f"{suffix}.pkl"
    if not pkl_path.exists():
        print(f"Файл {pkl_path} не найден")
        return

    data = joblib.load(pkl_path)
    models = data.get('models', {})
    metrics = data.get('metrics', {})
    mode_map = {
        'additive': 'Аддитивный',
        'multiplicative': 'Мультипликативный'
    }

    for fire_type, model in models.items():
        info = metrics.get(fire_type, {})
        # param_info = info.get('params', {})
        # mae = info.get('holdout_mae', info.get('mae', None))
        # if "no_anomaly" not in suffix:
        #     anomaly_coef = model.extra_regressors['anomaly']['prior_scale']
        # else:
        #     anomaly_coef = None
        # cols = {
        #     'Масштаб перегиба': param_info.get('changepoint_prior_scale'),
        #     'Масштаб сезонности': param_info.get('seasonality_prior_scale'),
        #     'Режим сезонности': mode_map.get(param_info.get('seasonality_mode'), ''),
        #     'Доверительный интервал': param_info.get('interval_width'),
        #     'MAE': round(mae, 5)
        # }
        # if anomaly_coef is not None:
        #     cols['Коэффициент аномалии'] = anomaly_coef
        # df_params = pd.DataFrame([cols], index=[fire_type])
        # n_cols = len(df_params.columns)
        # fig_t, ax_t = plt.subplots(figsize=(1.5 * n_cols, 1 + 0.4))
        # ax_t.axis('off')
        # tbl = ax_t.table(
        #     cellText=df_params.values,
        #     colLabels=df_params.columns,
        #     rowLabels=df_params.index,
        #     loc='center',
        #     cellLoc='center'
        # )
        # tbl.auto_set_font_size(False)
        # tbl.set_fontsize(8)
        # tbl.scale(1, 1.5)
        # try:
        #     tbl.auto_set_column_width(col=list(range(n_cols)))
        # except Exception:
        #     pass
        # fig_t.tight_layout()
        # table_path = PLOTS_DIR / f"params_{suffix}_{fire_type}.png"
        # fig_t.savefig(table_path, bbox_inches='tight')
        # plt.close(fig_t)

        history = model.history.copy()
        if transform_log:
            history['y'] = np.expm1(history['y'])
        last_date = model.history['ds'].max()
        end_date = pd.Timestamp('2024-12-31')
        n_months = (end_date.year - last_date.year) * 12 + (end_date.month - last_date.month)

        future = model.make_future_dataframe(periods=n_months, freq='ME')
        if hasattr(model, 'extra_regressors') and 'anomaly' in model.extra_regressors:
            future['anomaly'] = future['ds'].between(
                pd.Timestamp('2020-01-01'), pd.Timestamp('2021-09-30')
            ).astype(int)
        forecast = model.predict(future)
        if transform_log:
            for col in ['yhat', 'yhat_lower', 'yhat_upper']:
                forecast[col] = np.expm1(forecast[col])

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(history['ds'], history['y'], 'k.', label='Наблюдения')
        ax.plot(forecast['ds'], forecast['yhat'], label='Прогноз')
        ax.fill_between(
            forecast['ds'],
            forecast['yhat_lower'],
            forecast['yhat_upper'],
            alpha=0.3,
            label='Доверительный интервал'
        )
        title = f"{fire_type} - {'с учетом аномалии' if 'no_anomaly' not in suffix else 'без учета аномалии'}"
        if transform_log:
            title += ' (+лог-трансформация)'
        ax.set_title(title)
        ax.set_xlabel('Дата')
        ax.set_ylabel('Число пожаров')
        ax.grid(True)
        ax.legend(fontsize='small')

        graph_path = PLOTS_DIR / f"{suffix}_{fire_type}.png"
        fig.savefig(graph_path, bbox_inches='tight')
        plt.close(fig)




if __name__ == '__main__':
    # transform_log = True
    # train_for_region('RU-SA')
    # show_metrics("RU-SA_anomaly_log", transform_log = True)
    # show_metrics("RU-SA_anomaly", transform_log=False)
    # show_metrics("RU-SA_no_anomaly_log", transform_log=True)
    # show_metrics("RU-SA_no_anomaly", transform_log=False)
    # train_for_region("RU-PRI")
    # show_metrics("RU-PRI_anomaly", transform_log=False)
    # show_metrics("RU-PRI_no_anomaly", transform_log=False)
    # pass
    region_to_code = {
    'Adygey': 'RU-AD',
    'Altay': 'RU-ALT',  # Алтайский край
    'Amur': 'RU-AMU',
    "Arkhangel'sk": 'RU-ARK',
    "Astrakhan'": 'RU-AST',
    'Bashkortostan': 'RU-BA',
    'Belgorod': 'RU-BEL',
    'Bryansk': 'RU-BRY',
    'Buryat': 'RU-BU',
    'Chechnya': 'RU-CE',
    'Chelyabinsk': 'RU-CHE',
    'Chukot': 'RU-CHU',  
    'Chuvash': 'RU-CU',
    'City of St. Petersburg': 'RU-SPE',
    'Dagestan': 'RU-DA',
    'Gorno-Altay': 'RU-RAL',  # Республика Алтай
    'Ingush': 'RU-IN',
    'Irkutsk': 'RU-IRK',
    'Ivanovo': 'RU-IVA',
    'Kabardin-Balkar': 'RU-KB',
    'Kaliningrad': 'RU-KGD',
    'Kalmyk': 'RU-KL',
    'Kaluga': 'RU-KLU',
    'Kamchatka': 'RU-KAM',
    'Karachay-Cherkess': 'RU-KC',
    'Karelia': 'RU-KR',
    'Kemerovo': 'RU-KEM',
    'Khabarovsk': 'RU-KHA',
    'Khakass': 'RU-KK',
    'Khanty-Mansiy': 'RU-KHM',
    'Kirov': 'RU-KIR',
    'Komi': 'RU-KO',
    'Kostroma': 'RU-KOS',
    'Krasnodar': 'RU-KDA',
    'Krasnoyarsk': 'RU-KYA',
    'Kurgan': 'RU-KGN',
    'Kursk': 'RU-KRS',
    'Leningrad': 'RU-LEN',
    'Lipetsk': 'RU-LIP',
    'Magadan': 'RU-MAG',
    'Mariy-El': 'RU-ME',
    'Mordovia': 'RU-MO',
    'Moscow City': 'RU-MOW',  # город Москва
    'Moskva': 'RU-MOS',  # Московская область
    'Murmansk': 'RU-MUR',
    'Nenets': 'RU-NEN',
    'Nizhegorod': 'RU-NIZ',
    'North Ossetia': 'RU-SE',
    'Novgorod': 'RU-NGR',
    'Novosibirsk': 'RU-NVS',
    'Omsk': 'RU-OMS',
    'Orel': 'RU-ORL',
    'Orenburg': 'RU-ORE',
    'Penza': 'RU-PNZ',
    "Perm'": 'RU-PER',
    "Primor'ye": 'RU-PRI',
    'Pskov': 'RU-PSK',
    'Rostov': 'RU-ROS',
    'Ryazan': 'RU-RYA',
    'Sakha': 'RU-SA',
    'Sakhalin': 'RU-SAK',
    'Samara': 'RU-SAM',
    'Saratov': 'RU-SAR',
    'Smolensk': 'RU-SMO',
    "Stavropol'": 'RU-STA',
    'Sverdlovsk': 'RU-SVE',
    'Tambov': 'RU-TAM',
    'Tatarstan': 'RU-TA',
    'Tomsk': 'RU-TOM',
    'Tula': 'RU-TUL',
    'Tuva': 'RU-TY',
    "Tver'": 'RU-TVE',  # Возможная путаница с кавычками
    "Tyumen'": 'RU-TYU',  # Возможная путаница с кавычками
    'Udmurt': 'RU-UD',
    "Ul'yanovsk": 'RU-ULY',  # Возможная путаница с кавычками
    'Vladimir': 'RU-VLA',
    'Volgograd': 'RU-VGG',
    'Vologda': 'RU-VLG',
    'Voronezh': 'RU-VOR',
    'Yamal-Nenets': 'RU-YAN',
    "Yaroslavl'": 'RU-YAR',  # Возможная путаница с кавычками
    'Yevrey': 'RU-YEV',
    "Zabaykal'ye": 'RU-ZAB'
}
    # for value in region_to_code.values():
    #     if value != "RU-SA":
    #         train_for_region(value)

    # show_metrics("RU-PRI_no_anomaly", transform_log=False)
    for value in region_to_code.values():
        show_metrics(value + "_no_anomaly", transform_log=False)
        show_metrics(value + "_anomaly", transform_log=False)
    
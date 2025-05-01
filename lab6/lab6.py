import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import csv
import os
import re

def process_csv(csv_file: str, tag):
    try:
        df = pd.read_csv(csv_file, sep=';', dtype={'filename': str})
        
        required_columns = {'filename', 'Xi-square', 'RS-analyse', 'AUMP'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"Отсутствуют обязательные столбцы: {missing}")
        
        if df['filename'].isnull().any():
            raise ValueError("Обнаружены пустые значения в столбце 'filename'")
        
        empty_mask = ~df['filename'].str.contains('_stego', na=False)
        empty_df = df[empty_mask]
        filled_df = df[~empty_mask]
        
        methods = ['Xi-square', 'RS-analyse', 'AUMP']
        fp_rates = []
        fn_rates = []
        
        for method in methods:
            fp = empty_df[empty_df[method] == 1].shape[0]
            fp_rate = fp / len(empty_df) if len(empty_df) > 0 else 0
            fp_rates.append(fp_rate)
            
            fn = filled_df[filled_df[method] == 0].shape[0]
            fn_rate = fn / len(filled_df) if len(filled_df) > 0 else 0
            fn_rates.append(fn_rate)
        
        x = range(len(methods))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.canvas.manager.set_window_title(f'График №{tag}')
        bars1 = ax.bar(x, fp_rates, width, label='False Positive', color='#ff6b6b')
        bars2 = ax.bar([i + width for i in x], fn_rates, width, label='False Negative', color='#4ecdc4')
        
        ax.set_ylabel('Доля ошибок', fontsize=12)
        ax.set_title('Сравнение ошибок детектирования по методам', fontsize=14)
        ax.set_xticks([i + width/2 for i in x])
        ax.set_xticklabels(methods)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        for bars in (bars1, bars2):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1%}',
                            xy=(bar.get_x() + bar.get_width()/2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
        
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Ошибка обработки: {str(e)}")
        print("Требуемые параметры CSV:")
        print("- Столбец 'filename' с маркировкой '_stego' для заполненных контейнеров")
        print("- Числовые столбцы методов (0=не обнаружено, 1=обнаружено)")

def parse_file(file_path):
    results = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        
        blocks = re.split(r"Результаты стегоанализа для", content)
        
        for block in blocks[1:]:
            chi_square = rs_analysis = aump = None
            image_path = None
            
            image_path_match = re.search(r"(/[\w/._-]+\.\w+)", block)  # Путь к изображению (например, /path/to/2.bmp)
            if image_path_match:
                image_path = image_path_match.group(1)
                image_filename = os.path.basename(image_path)
            
            chi_square_match = re.search(r"Хи-квадрат \(среднее по всем блокам\): ([\d\.]+)", block)
            rs_analysis_match = re.search(r"RS-анализ: ([\d\.E-]+)", block)
            aump_match = re.search(r"AUMP-показатель: ([\d\.]+)", block)
            
            if chi_square_match:
                chi_square = float(chi_square_match.group(1))
            if rs_analysis_match:
                rs_analysis = float(rs_analysis_match.group(1))
            if aump_match:
                aump = float(aump_match.group(1))
            
            results.append((image_filename, chi_square, rs_analysis, aump))
    
    return results

def compare_with_thresholds(chi_square, rs_analysis, aump, chi_threshold, rs_threshold, aump_threshold):
    """Функция для сравнения значений с порогами."""
    chi_square_check = 1 if chi_square >= chi_threshold else 0
    rs_analysis_check = 1 if rs_analysis <= rs_threshold else 0
    aump_check = 1 if aump <= aump_threshold else 0
    return chi_square_check, rs_analysis_check, aump_check

def read_files(file_paths):
    not_processed_results = []
    for file_path in file_paths:
        if os.path.exists(file_path):  # Проверка существования файла
            pased = parse_file(file_path)
            for _, (image_filename, chi_square, rs_analysis, aump) in enumerate(pased):
                not_processed_results.append([image_filename, chi_square, rs_analysis, aump])
    return not_processed_results

def perocess_results(chi_threshold, rs_threshold, aump_threshold, not_processed_results):
    processed_results = []
    for _, (image_filename, chi_square, rs_analysis, aump) in enumerate(not_processed_results):
        # Сравниваем с порогами
        chi_check, rs_check, aump_check = compare_with_thresholds(chi_square, rs_analysis, aump, chi_threshold, rs_threshold, aump_threshold)
        processed_results.append([image_filename, chi_check, rs_check, aump_check])
    return processed_results

def write_to_csv(output_csv, processed_results):
    header = ['filename', 'Xi-square', 'RS-analyse', 'AUMP']
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(header)
        for _, (image_filename, chi_square, rs_analysis, aump) in enumerate(processed_results):
            writer.writerow([image_filename, chi_square, rs_analysis, aump])

if __name__ == "__main__":
    file_paths = [
        'empty.txt',
        'stego_lab3.txt',
        'stego_lab4.txt'
    ]

    not_processed_results = read_files(file_paths)

    methods = ['Xi-square', 'RS-analyse', 'AUMP']

    def calculate_fp_fn(processed_results):
        df = pd.DataFrame(processed_results, columns=['filename', 'Xi-square', 'RS-analyse', 'AUMP'])
        empty_mask = ~df['filename'].str.contains('_stego', na=False)
        filled_mask = df['filename'].str.contains('_stego', na=False)

        fp_rates = {}
        fn_rates = {}

        for method in methods:
            fp = df.loc[empty_mask, method].sum()
            fp_rate = fp / empty_mask.sum() if empty_mask.sum() > 0 else 0
            fn = (df.loc[filled_mask, method] == 0).sum()
            fn_rate = fn / filled_mask.sum() if filled_mask.sum() > 0 else 0

            fp_rates[method] = fp_rate
            fn_rates[method] = fn_rate

        return fp_rates, fn_rates

    ### График для метода Xi-square ###
    chi_thresholds = np.arange(13000, 0, -1000)
    fp_list = []
    fn_list = []
    thresholds = []

    for thr in chi_thresholds:
        processed = []
        for row in not_processed_results:
            filename, chi, rs, aump = row
            chi_check = 1 if chi >= thr else 0
            rs_check = 0
            aump_check = 0
            processed.append([filename, chi_check, rs_check, aump_check])
        fp_rates, fn_rates = calculate_fp_fn(processed)
        fp_list.append(fp_rates['Xi-square'])
        fn_list.append(fn_rates['Xi-square'])
        thresholds.append(thr)

    plt.figure(figsize=(7, 6))
    sc = plt.scatter(fn_list, fp_list, c=thresholds, cmap='plasma', edgecolors='k', s=50, alpha=0.8)
    plt.colorbar(sc, label='Пороговое значение')
    plt.xlabel('Ошибка второго рода (False Negative)')
    plt.ylabel('Ошибка первого рода (False Positive)')
    plt.title('Ошибки для метода Xi-square')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    ### График для метода RS-analyse ###
    rs_thresholds = np.arange(2, 0, -0.001)
    fp_list = []
    fn_list = []
    thresholds = []

    for thr in rs_thresholds:
        processed = []
        for row in not_processed_results:
            filename, chi, rs, aump = row
            chi_check = 0
            rs_check = 1 if rs <= thr else 0
            aump_check = 0
            processed.append([filename, chi_check, rs_check, aump_check])
        fp_rates, fn_rates = calculate_fp_fn(processed)
        fp_list.append(fp_rates['RS-analyse'])
        fn_list.append(fn_rates['RS-analyse'])
        thresholds.append(thr)

    plt.figure(figsize=(7, 6))
    sc = plt.scatter(fn_list, fp_list, c=thresholds, cmap='plasma', edgecolors='k', s=50, alpha=0.8)
    plt.colorbar(sc, label='Пороговое значение')
    plt.xlabel('Ошибка второго рода (False Negative)')
    plt.ylabel('Ошибка первого рода (False Positive)')
    plt.title('Ошибки для метода RS-analyse')
    plt.grid(True)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.show()

    ### График для метода AUMP ###
    aump_thresholds = np.arange(10, 0, -0.1)
    fp_list = []
    fn_list = []
    thresholds = []

    for thr in aump_thresholds:
        processed = []
        for row in not_processed_results:
            filename, chi, rs, aump = row
            chi_check = 0
            rs_check = 0
            aump_check = 1 if aump <= thr else 0
            processed.append([filename, chi_check, rs_check, aump_check])
        fp_rates, fn_rates = calculate_fp_fn(processed)
        fp_list.append(fp_rates['AUMP'])
        fn_list.append(fn_rates['AUMP'])
        thresholds.append(thr)

    plt.figure(figsize=(7, 6))
    sc = plt.scatter(fn_list, fp_list, c=thresholds, cmap='plasma', edgecolors='k', s=50, alpha=0.8)
    plt.colorbar(sc, label='Пороговое значение')
    plt.xlabel('Ошибка второго рода (False Negative)')
    plt.ylabel('Ошибка первого рода (False Positive)')
    plt.title('Ошибки для метода AUMP')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    chi_threshold = 5000
    rs_threshold = 0.02
    aump_threshold = 1.9

    processed_results = perocess_results(chi_threshold, rs_threshold, aump_threshold, not_processed_results)
    write_to_csv('analysis_results.csv', processed_results)
    process_csv('analysis_results.csv', 'Best')

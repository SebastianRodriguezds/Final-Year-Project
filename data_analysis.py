import pandas as pd

# Cargar los datos
data = pd.read_csv('employee_data.csv')

def get_average_metrics_for_month(month: str):
    # Convertir la columna 'month' a tipo datetime
    data['month'] = pd.to_datetime(data['month'], format='%Y-%m-%d')
    
    # Extraer solo el mes y el año de las fechas en 'month'
    data['month_str'] = data['month'].dt.strftime('%Y-%m')  # Solo año y mes (sin día)
    
    # Filtrar los datos por el mes deseado
    month_data = data[data['month_str'] == month]
    
    # Si no hay datos para el mes seleccionado, retornar un DataFrame vacío
    if month_data.empty:
        print("No se encontraron datos para este mes.")
        return pd.DataFrame()  # Si no hay datos, retorna un DataFrame vacío
    
    # Asegurarse de que las columnas necesarias son numéricas y no contienen valores nulos
    month_data.loc[:, 'task_response_time'] = pd.to_numeric(month_data['task_response_time'], errors='coerce').fillna(0)
    month_data.loc[:, 'email_response_time'] = pd.to_numeric(month_data['email_response_time'], errors='coerce').fillna(0)
    month_data.loc[:, 'tasks_completed'] = pd.to_numeric(month_data['tasks_completed'], errors='coerce').fillna(0)

    # Agrupar por departamento y calcular promedios de las métricas
    avg_metrics = month_data.groupby('department').agg({
        'work_hours': 'mean',                
        'task_response_time': 'mean',        
        'email_response_time': 'mean',       
        'tasks_completed': 'mean',           
        'meetings_attended': 'mean',         
        'collaboration_score': 'mean',       
        'time_off': 'mean'                   
    }).reset_index()

    # Redondear los resultados a 2 decimales
    avg_metrics = avg_metrics.round({
        'work_hours': 2,
        'task_response_time': 2,
        'email_response_time': 2,
        'tasks_completed': 2,
        'meetings_attended': 2,
        'collaboration_score': 2,
        'time_off': 2
    })
    
    return avg_metrics

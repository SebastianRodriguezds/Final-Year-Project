import pandas as pd
from data_analysis import get_average_metrics_for_month

# Cargar las reglas predefinidas desde el CSV
def load_rules():
    return pd.read_csv('rules.csv')

# Genera mensajes consolidados por departamento
def check_metrics_against_rules(month: str):
    metrics = get_average_metrics_for_month(month)
    print(f"METRICS HEADS: {metrics.head()}")
    if metrics.empty:
        return []

    rules = load_rules()
    alerts_by_department = {}
    
    departments = metrics['department'].unique()
    
    for department in departments:
        department_metrics = metrics[metrics['department'] == department]
        department_alerts = []
        
        # List of all metrics we want to check for
        all_metrics = ['overtime_hours','task_completion_time', 'meetings_hours', 'time_off', 'email_response_time']
        
        for metric in all_metrics:
            # Intentar obtener el valor de la métrica con manejo de posibles valores ausentes
            if metric in department_metrics.columns:
                value = department_metrics[metric].iloc[0]  # Obtener el primer valor de la columna
            else:
                value = None  # Si la métrica no existe, asignamos None

            rule = rules[(rules['department'] == department) & (rules['metric'] == metric)]
            
            if rule.empty:
                continue  # Skip if there's no rule for this department/metric
            
            threshold = rule['threshold'].values[0]
            alert_type = rule['alert_type'].values[0]
            
            # Generar el mensaje de alerta según la métrica
            alert_message = ""
            if metric == 'overtime_hours':
                if value is not None:
                    if value > threshold:
                        alert_message = f"High overtime hours ({value}), suggesting high motivation."
                    elif value == threshold:
                        alert_message = f"Moderate overtime hours ({value}), suggesting neutral motivation."
                    else:
                        alert_message = f"Low overtime hours ({value}), suggesting low motivation."
                else:
                    alert_message = f"No overtime data for this department."
            
            elif metric == 'meetings_hours':
                if value is not None:
                    if value > threshold:
                        alert_message = f"High meetings hours ({value}), suggesting high burnout risk."
                    elif value == threshold:
                        alert_message = f"Moderate meetings hours ({value}), suggesting moderate burnout risk."
                    else:
                        alert_message = f"Low meetings hours ({value}), suggesting low burnout risk."
                else:
                    alert_message = f"No meetings data for this department."
            
            elif metric == 'time_off':
                if value is not None:
                    if value < threshold:
                        alert_message = f"Low time off ({value} days), suggesting high motivation."
                        alert_type = "High Motivation"
                    else:
                        alert_message = f"High time off ({value} days), suggesting low motivation."
                else:
                    alert_message = f"No time off data for this department."
                    alert_type = "N/A"
            
            elif metric == 'email_response_time':
                if value is not None:
                    if value < 4:
                        alert_message = f"Good email response time ({value} hours), indicating positive engagement."
                    elif value > 6:
                        alert_message = f"High email response time ({value} hours), suggesting possible disengagement."
                    else:
                        alert_message = f"Moderate email response time ({value} hours), indicating neutral engagement."
                else:
                    alert_message = f"No email response time data for this department."
            
            elif metric == "task_completion_time":
                if value is not None:
                    if value > 20:
                        alert_message = f"High number of tasks completed ({value}), suggesting good productivity."

                    elif value < 15:
                        alert_message = f"Low number of tasks completed ({value}), indicating possible disengagement."
                    else:
                        alert_message = f"Moderate number of tasks completed ({value}), suggesting neutral productivity."
                else:
                    alert_message = f"No tasks completed data for this department."
            
            # Agregar la alerta generada
            department_alerts.append({
                'alert': alert_message,
                'metric': metric,
                'value': value if value is not None else 'N/A',
                'threshold': threshold,
                'alert_type': alert_type
            })
        
        # Agregar las alertas si existen
        if department_alerts:
            alerts_by_department[department] = department_alerts
    
    return alerts_by_department

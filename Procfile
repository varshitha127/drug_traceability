web: gunicorn DrugTraceApp.wsgi:application --log-file -
worker: python manage.py process_tasks 
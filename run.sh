source .env
celery -A cyads_transparency_web worker -l info &
sleep 3
celery flower -A cyads_transparency_web --broker=redis://localhost:6379// &
python manage.py runserver &

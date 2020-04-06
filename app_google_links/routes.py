import views
from settings import BASE_DIR


def setup_routes(app):
    app.router.add_get('/', views.index, name='index')
    app.router.add_get('/login', views.login, name='login')
    app.router.add_post('/login', views.login, name='login')
    app.router.add_get('/signup', views.signup, name='signup')
    app.router.add_post('/signup', views.signup, name='signup')
    app.router.add_post('/create', views.index, name='create')
    app.router.add_post('/del_link/{id4del_link}', views.index,
                        name='del_link')
    app.router.add_post('/del_account', views.index, name='del_account')
    app.router.add_post('/change_password', views.index,
                        name='change_password')
    app.router.add_get('/logout', views.logout, name='logout')
    setup_static_routes(app)


def setup_static_routes(app):
    app.router.add_static('/static/',
                          path=BASE_DIR / 'app_google_links' / 'static',
                          name='static')

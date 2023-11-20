from django.urls import path

from management import views


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login', views.LoginView.as_view(), name='login'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('boards', views.BoardsView.as_view(), name='boards'),
    path('register', views.RegisterBoard.as_view(), name='register'),
    path('ping/<int:device_id>', views.PingView.as_view(), name='ping'),
    path('updateBoards', views.UpdateView.as_view(), name='update'),
    path('firmwareUpdateComplete/<int:board_id>', views.FirmwareUpdateCompleteView.as_view(), name='firmware_update_complete'),
    path('settings', views.SettingsView.as_view(), name='settings'),
    path('settingsApi', views.SettingsApiView.as_view(), name='settings_api'),
]

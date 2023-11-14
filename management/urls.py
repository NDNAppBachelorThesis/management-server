from django.urls import path

from management import views


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('boards', views.BoardsView.as_view(), name='boards'),
    path('register', views.RegisterBoard.as_view(), name='register'),
    path('ping/<int:device_id>', views.PingView.as_view(), name='ping'),
    path('updateBoards', views.UpdateView.as_view(), name='update'),
    path('firmwareUpdateComplete/<int:board_id>', views.FirmwareUpdateCompleteView.as_view(), name='firmware_update_complete'),
]

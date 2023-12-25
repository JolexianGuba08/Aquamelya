from django.urls import path
from . import views

urlpatterns = [
    # SUPPLY SECTION
    path('supply/', views.InventorySupplyIndexView.as_view(), name='inventory_supply_view'),
    path('supply/add/', views.InventorySupplyCreateView.as_view(), name='add_supply'),
    path('supply/delete/<str:pk>', views.InventorySupplyDeleteView.as_view(), name='delete_supply'),
    path('supply/update/<str:pk>', views.InventorySupplyUpdateView.as_view(), name='update_supply_info'),
    # ASSET SECTION
    path('assets/', views.InventoryAssetIndex.as_view(), name='inventory_assets_view'),
    path('assets/add/', views.InventoryAssetsCreateView.as_view(), name='add_asset'),
    path('assets/delete/<str:pk>', views.InventoryAssetDeleteView.as_view(), name='delete_asset'),
    path('assets/update/<str:pk>', views.InventoryAssetUpdateView.as_view(), name='update_asset_info'),
    path('assets/view/json/', views.asset_json, name='get_asset_json')
]

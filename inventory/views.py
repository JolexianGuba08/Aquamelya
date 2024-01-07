from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import generic, View
from inventory.forms import AssetModelForm, SupplyModelForm, UpdateAssetModelForm, UpdateSupplyModelForm
from inventory.models import Assets, Supply, AssetType, SupplyType
from management.models import Supplier


# --------- SUPPLY SECTION ------------ #
# Suppy Inventory Table

class InventorySupplyIndexView(generic.ListView):
    model = Supply
    context_object_name = 'supplies'
    template_name = 'aqua_supply/supply_view.html'

    def get_queryset(self):
        qs = super().get_queryset().exclude(supply_status=2).order_by('-supply_date_added')
        if 'type' in self.request.GET:
            qs = qs.filter(supply_type=int(self.request.GET['type']))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        supply_type = get_list_or_404(SupplyType)
        suppliers = get_list_or_404(Supplier, supplier_status=1)
        # Add the data to the context
        context['supply_type'] = supply_type
        context['suppliers'] = suppliers
        return context

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


# Suppy Inventory DELETE MODAL
class InventorySupplyDeleteView(View):
    template_name = 'aqua_supply/delete_supply.html'  # Replace with your confirmation template

    def get(self, request, pk):
        supply = get_object_or_404(Supply, pk=pk)
        return render(request, self.template_name, {'supply': supply})

    def post(self, request, pk):
        supply = get_object_or_404(Supply, pk=pk)
        # Check if the user confirmed the deletion
        if request.POST.get('confirm') == 'delete':
            supply.supply_status = 2  # 'DELETED' status
            try:
                messages.success(request, 'Supply was successfully deleted.')
                supply.save()
                return redirect('inventory_supply_view')
            except Exception as e:
                # Handle the exception as needed
                return HttpResponseBadRequest(f'Error: {str(e)}')
        else:
            # User chose not to delete, redirect or render another template as needed
            messages.error(request, 'Supply was successfully deleted.')
            return redirect('inventory_supply_view')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


# Suppy Inventory CREATE MODAL
class InventorySupplyCreateView(BSModalCreateView):
    template_name = 'aqua_supply/add_supply.html'
    form_class = SupplyModelForm
    success_message = 'Success: Supply was created.'
    success_url = reverse_lazy('inventory_supply_view')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


# Suppy Inventory UPDATE MODAL
class InventorySupplyUpdateView(BSModalUpdateView):
    template_name = 'aqua_supply/update_supply.html'
    model = Supply
    form_class = UpdateSupplyModelForm
    success_message = 'Success: Supply was updated.'
    success_url = reverse_lazy('inventory_supply_view')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Fetch supply_on_hand value explicitly from the database
        instance = self.get_object()
        kwargs['instance'] = instance  # Update the form instance to include supply_on_hand
        return kwargs


# --------- ASSET SECTION ------------ #
# Asset Inventory Table
class InventoryAssetIndex(generic.ListView):
    model = Assets
    context_object_name = 'asset'
    template_name = 'aqua_assets/assets_view.html'

    def get_queryset(self):
        qs = super().get_queryset().exclude(asset_status=2).order_by('-asset_id')
        if 'type' in self.request.GET:
            qs = qs.filter(asset_type=int(self.request.GET['type']))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Query objects for AnotherModel
        asset_type = AssetType.objects.all()
        # Add the data to the context
        context['asset_type'] = asset_type

        return context

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


# Asset Inventory DELETE MODAL
class InventoryAssetDeleteView(View):
    template_name = 'aqua_assets/delete_asset.html'  # Replace with your confirmation template

    def get(self, request, pk):
        asset = get_object_or_404(Assets, pk=pk)
        return render(request, self.template_name, {'asset': asset})

    def post(self, request, pk):
        asset = get_object_or_404(Assets, pk=pk)
        # Check if the user confirmed the deletion
        if request.POST.get('confirm') == 'delete':
            asset.asset_status = 2  # 'DELETED' status
            try:
                messages.success(request, 'Asset was successfully deleted.')
                asset.save()
                return redirect('inventory_assets_view')
            except Exception as e:
                # Handle the exception as needed
                return HttpResponseBadRequest(f'Error: {str(e)}')
        else:
            # User chose not to delete, redirect or render another template as needed
            messages.error(request, 'Asset was successfully deleted.')
            return redirect('inventory_assets_view')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


# Asset Inventory UPDATE MODAL
class InventoryAssetUpdateView(BSModalUpdateView):
    model = Assets
    template_name = 'aqua_assets/update_asset.html'
    form_class = UpdateAssetModelForm
    success_message = 'Success: Asset was updated successfullly.'
    success_url = reverse_lazy('inventory_assets_view')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


# Asset Inventory CREATE MODAL
class InventoryAssetsCreateView(BSModalCreateView):
    template_name = 'aqua_assets/add_asset.html'
    form_class = AssetModelForm
    success_message = 'Success: Asset was created.'
    success_url = reverse_lazy('inventory_assets_view')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


# Asset Inventory Landing

def asset_json(request):
    if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
        raise Http404("You are not allowed to access this page.")
    data = {}
    try:
        if request.method == 'GET':
            assets = Assets.objects.all()
            data['table'] = render_to_string(
                'aqua_assets/_asset_table.html',
                {'asset': assets},
                request=request
            )
            return JsonResponse(data)
    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error: {e}")
        data['error'] = str(e)
        return JsonResponse(data, status=500)

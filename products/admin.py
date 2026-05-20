# products/admin.py
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from .models import Product, Category, SubCategory, Wishlist

class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'brand', 'price', 'stock', 'gender', 'is_featured']
    list_filter = ['category', 'gender', 'is_featured', 'brand']
    search_fields = ['name', 'brand', 'description']
    list_editable = ['price', 'stock', 'is_featured']
    
    def delete_model(self, request, obj):
        """Override delete to show friendly error message"""
        try:
            obj.delete()
            messages.success(request, f"✅ Product '{obj.name}' deleted successfully.")
        except ValidationError as e:
            messages.error(request, f"❌ {str(e)}")
        except ProtectedError:
            messages.error(
                request, 
                f"❌ Cannot delete '{obj.name}' because it has existing orders. "
                f"Please cancel or complete the orders first."
            )
    
    def delete_queryset(self, request, queryset):
        """Handle bulk delete with proper error messages"""
        deleted_count = 0
        error_count = 0
        
        for obj in queryset:
            try:
                obj.delete()
                deleted_count += 1
            except (ValidationError, ProtectedError) as e:
                error_count += 1
                self.message_user(request, f"❌ Cannot delete '{obj.name}': {str(e)}", messages.ERROR)
        
        if deleted_count > 0:
            messages.success(request, f"✅ Successfully deleted {deleted_count} product(s).")
        if error_count > 0:
            messages.error(request, f"⚠️ Failed to delete {error_count} product(s) due to pending orders.")
    
    actions = ['delete_selected_products_with_check']
    
    def delete_selected_products_with_check(self, request, queryset):
        """Custom action that shows which products can/cannot be deleted"""
        can_delete = []
        cannot_delete = []
        
        for product in queryset:
            pending_orders = product.orderitem_set.filter(
                order__status__in=['pending', 'confirmed']
            ).exists()
            
            if pending_orders:
                cannot_delete.append(product.name)
            else:
                can_delete.append(product.name)
        
        if cannot_delete:
            self.message_user(
                request, 
                f"⚠️ Cannot delete these products (have pending orders): {', '.join(cannot_delete)}", 
                messages.ERROR
            )
        
        if can_delete:
            # Delete the products that can be deleted
            Product.objects.filter(name__in=can_delete).delete()
            self.message_user(
                request, 
                f"✅ Deleted: {', '.join(can_delete)}", 
                messages.SUCCESS
            )
    
    delete_selected_products_with_check.short_description = "Delete selected (checks orders first)"

# Register your models
admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Wishlist)
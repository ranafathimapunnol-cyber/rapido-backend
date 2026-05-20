# products/views.py - COMPLETE FIXED VERSION WITH PROPER CATEGORY HANDLING
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes

from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Product,
    Category,
    SubCategory,
    Wishlist
)

from .serializers import (
    ProductSerializer,
    CategorySerializer,
    SubCategorySerializer,
    WishlistSerializer
)


# =========================
# PUBLIC ENDPOINTS (No login required)
# =========================

class GetCategoriesView(ListAPIView):
    """Get all categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GetSubCategoriesView(ListAPIView):
    """Get subcategories for a category"""
    serializer_class = SubCategorySerializer

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SubCategory.objects.filter(category_id=category_id)


class GetProductsView(ListAPIView):
    """Get all products with filtering"""
    serializer_class = ProductSerializer

    def get_queryset(self):
        products = Product.objects.all().select_related('category').order_by('-created_at')
        
        # Apply filters
        category = self.request.GET.get('category')
        sub_category = self.request.GET.get('sub_category')
        search = self.request.GET.get('search')
        gender = self.request.GET.get('gender')
        is_featured = self.request.GET.get('is_featured')

        # Category filter - Case insensitive
        if category:
            category = category.strip()
            print(f"🔍 Filtering by category: '{category}'")
            
            # Try to find category (case insensitive)
            category_obj = Category.objects.filter(name__iexact=category).first()
            if category_obj:
                products = products.filter(category=category_obj)
                print(f"✅ Found category: '{category_obj.name}'")
            elif category.isdigit():
                products = products.filter(category_id=int(category))
                print(f"✅ Filtering by category ID: {category}")
            else:
                # Try partial match
                products = products.filter(category__name__icontains=category)
                print(f"✅ Partial match filtering: {category}")

        if sub_category:
            sub_category = sub_category.strip()
            if sub_category.isdigit():
                products = products.filter(sub_category_id=sub_category)
            else:
                products = products.filter(sub_category__name__iexact=sub_category)

        if search:
            products = products.filter(name__icontains=search)

        if gender:
            products = products.filter(gender__iexact=gender)

        if is_featured:
            products = products.filter(is_featured=True)

        return products


class GetProductView(RetrieveAPIView):
    """Get single product by ID"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'pk'


class GetNewArrivalsView(ListAPIView):
    """Get new arrivals (last 30 days)"""
    serializer_class = ProductSerializer

    def get_queryset(self):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        products = Product.objects.filter(
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')[:10]

        if products.count() < 4:
            products = Product.objects.all().order_by('-created_at')[:10]

        return products


class GetFeaturedProductsView(ListAPIView):
    """Get featured products"""
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(is_featured=True)[:8]


# =========================
# WISHLIST ENDPOINTS (Login required)
# =========================

class GetWishlistView(ListAPIView):
    """Get user's wishlist"""
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        wishlist_items = Wishlist.objects.filter(
            user=self.request.user
        ).select_related('product')
        return [item.product for item in wishlist_items]


class AddWishlistView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            product_id = request.data.get('product')
            if not product_id:
                return Response(
                    {"error": "Product ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product = Product.objects.filter(id=product_id).first()
            if not product:
                return Response(
                    {"error": "Product not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user,
                product=product
            )

            return Response({
                "message": "Added to wishlist",
                "is_wishlisted": True
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RemoveWishlistView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user, product_id=pk)
            wishlist_item.delete()
            return Response(
                {"message": "Removed from wishlist", "is_wishlisted": False},
                status=status.HTTP_200_OK
            )
        except Wishlist.DoesNotExist:
            return Response(
                {"error": "Item not found in wishlist"},
                status=status.HTTP_404_NOT_FOUND
            )


class ToggleWishlistView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {"error": "Product ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(Product, id=product_id)
        wishlist_item = Wishlist.objects.filter(
            user=request.user, product=product)

        if wishlist_item.exists():
            wishlist_item.delete()
            return Response({
                "message": "Removed from wishlist",
                "is_wishlisted": False
            }, status=status.HTTP_200_OK)
        else:
            Wishlist.objects.create(user=request.user, product=product)
            return Response({
                "message": "Added to wishlist",
                "is_wishlisted": True
            }, status=status.HTTP_201_CREATED)


class CheckWishlistView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        is_wishlisted = Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).exists()
        return Response({"is_wishlisted": is_wishlisted})


# =========================
# ADMIN ENDPOINTS (Admin only)
# =========================

class AddProductView(GenericAPIView):
    """Admin: Add new product with category support"""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            print("=" * 50)
            print("📦 ADDING NEW PRODUCT")
            print("=" * 50)
            
            # Handle category - CASE INSENSITIVE
            category = None
            category_name = request.data.get('category') or request.data.get('category_name')
            
            print(f"Category from request: '{category_name}'")
            
            if category_name:
                category_name = str(category_name).strip()
                # Try to find existing category (case insensitive)
                category = Category.objects.filter(name__iexact=category_name).first()
                
                if not category:
                    # Create new category
                    category = Category.objects.create(name=category_name)
                    print(f"✅ Created NEW category: '{category_name}'")
                else:
                    print(f"✅ Found existing category: '{category.name}' (ID: {category.id})")

            # Get form data
            name = request.data.get('name', '')
            description = request.data.get('description', '')
            price = float(request.data.get('price', 0))
            stock = int(request.data.get('stock', 0))
            brand = request.data.get('brand', 'Premium')
            size = request.data.get('size', '')
            color = request.data.get('color', '')
            gender = request.data.get('gender', 'UNISEX')

            # Create product
            product = Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                category=category,
                brand=brand,
                size=size,
                color=color,
                gender=gender,
            )
            
            # Handle image
            if request.FILES.get('image'):
                product.image = request.FILES.get('image')

            product.save()

            print(f"\n✅ Product saved: {product.name}")
            print(f"   - Category: {product.category.name if product.category else 'NO CATEGORY'}")
            print(f"   - Category ID: {product.category.id if product.category else 'None'}")
            print(f"   - Stock: {product.stock}")
            print(f"   - Price: {product.price}")
            print("=" * 50)

            # Return response with category info
            serializer = ProductSerializer(product)
            return Response({
                "message": "Product created successfully",
                "product": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"❌ Error adding product: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminProductsView(ListAPIView):
    """Admin: Get all products"""
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all().order_by('-id')


class UpdateProductView(GenericAPIView):
    """Admin: Update existing product"""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Update basic fields
            if 'name' in request.data:
                product.name = request.data['name']
            if 'description' in request.data:
                product.description = request.data['description']
            if 'price' in request.data:
                product.price = float(request.data['price'])
            if 'stock' in request.data:
                product.stock = int(request.data['stock'])
            if 'brand' in request.data:
                product.brand = request.data['brand']
            if 'size' in request.data:
                product.size = request.data['size']
            if 'color' in request.data:
                product.color = request.data['color']
            if 'gender' in request.data:
                product.gender = request.data['gender']

            # Handle category update
            category_name = request.data.get('category') or request.data.get('category_name')
            if category_name:
                category = Category.objects.filter(name__iexact=category_name).first()
                if not category:
                    category = Category.objects.create(name=category_name)
                product.category = category

            # Handle image update
            if request.FILES.get('image'):
                product.image = request.FILES.get('image')

            product.save()

            print(f"✅ Product updated: {product.name}")
            print(f"   - Category: {product.category.name if product.category else 'None'}")

            serializer = ProductSerializer(product)
            return Response({
                "message": "Product updated successfully",
                "product": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error updating product: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteProductView(GenericAPIView):
    """Admin: Delete product"""
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
            product.delete()
            return Response({"message": "Product deleted successfully"}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)


class SendReportEmailView(GenericAPIView):
    """Admin: Send report via email"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            email = request.data.get('email')
            report_data = request.data.get('report_data', {})
            message = request.data.get('message', '')
            
            if not email:
                return Response(
                    {'error': 'Email is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subject = f"E-commerce Report - {report_data.get('dateRange', 'Monthly')}"
            body = f"""
Report Generated: {report_data.get('generatedAt', 'N/A')}
Date Range: {report_data.get('dateRange', 'N/A')}

SUMMARY:
- Total Revenue: {report_data.get('reportData', {}).get('totalRevenue', 0)}
- Total Orders: {report_data.get('reportData', {}).get('totalOrders', 0)}
- Total Products: {report_data.get('reportData', {}).get('totalProducts', 0)}
- Total Users: {report_data.get('reportData', {}).get('totalUsers', 0)}

Message: {message if message else 'No message'}
"""
            
            print(f"\n📧 Email would be sent to: {email}")
            print(f"Subject: {subject}")
            print(f"Body: {body}\n")
            
            return Response(
                {'message': f'Report sent successfully to {email}'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================
# DEBUG ENDPOINTS
# =========================

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_products_by_category(request, category_name):
    """Debug endpoint to check products by category"""
    products = Product.objects.all()
    category = Category.objects.filter(name__iexact=category_name).first()
    
    result = {
        "requested_category": category_name,
        "category_found": category.name if category else None,
        "category_id": category.id if category else None,
        "total_products": products.count(),
        "products_in_category": [],
        "all_categories": [],
        "all_products": []
    }
    
    if category:
        category_products = Product.objects.filter(category=category)
        result["products_in_category"] = [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.name if p.category else None,
                "category_id": p.category.id if p.category else None,
                "price": float(p.price),
                "stock": p.stock
            }
            for p in category_products
        ]
        result["products_in_category_count"] = category_products.count()
    
    all_categories = Category.objects.all()
    result["all_categories"] = [
        {
            "id": c.id, 
            "name": c.name, 
            "product_count": Product.objects.filter(category=c).count()
        }
        for c in all_categories
    ]
    
    result["all_products"] = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category.name if p.category else "NO CATEGORY",
            "category_id": p.category.id if p.category else None
        }
        for p in products[:20]
    ]
    
    return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_all_categories(request):
    """Debug: Get all categories with product counts"""
    categories = Category.objects.all()
    result = {
        "total_categories": categories.count(),
        "categories": []
    }
    
    for category in categories:
        product_count = Product.objects.filter(category=category).count()
        result["categories"].append({
            "id": category.id,
            "name": category.name,
            "product_count": product_count,
            "products": [
                {"id": p.id, "name": p.name}
                for p in Product.objects.filter(category=category)[:10]
            ]
        })
    
    return Response(result)
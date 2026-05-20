# cart/views.py - CONVERTED TO GENERIC VIEWS (ALL FEATURES PRESERVED)
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Cart, CartItem
from .serializers import CartSerializer
from products.models import Product


# =========================
# GET CART - Generic View
# =========================
class GetCartView(RetrieveAPIView):
    """Get user's cart"""
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


# =========================
# ADD TO CART - Generic View (Preserves ALL logic)
# =========================
class AddToCartView(GenericAPIView):
    """Add item to cart (with quantity handling)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            cart, _ = Cart.objects.get_or_create(user=request.user)

            product_id = request.data.get('product')
            quantity = int(request.data.get('quantity', 1))

            if not product_id:
                return Response({"error": "Product ID missing"}, status=status.HTTP_400_BAD_REQUEST)

            product = Product.objects.filter(id=product_id).first()

            if not product:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            # ✅ PRESERVED: Get or create cart item logic
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product
            )

            # ✅ PRESERVED: Quantity update logic
            if not created:
                item.quantity += quantity
            else:
                item.quantity = quantity

            item.save()

            return Response({"message": "Item added successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# UPDATE CART ITEM - Generic View (Preserves ALL logic)
# =========================
class UpdateCartItemView(GenericAPIView):
    """Update cart item quantity"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            item_id = request.data.get('item_id')
            quantity = int(request.data.get('quantity', 1))

            # ✅ PRESERVED: Get item and update/delete logic
            item = CartItem.objects.get(id=item_id)

            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()

            return Response({"message": "Updated"}, status=status.HTTP_200_OK)

        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# REMOVE CART ITEM - Generic View (Preserves ALL logic)
# =========================
class RemoveCartItemView(GenericAPIView):
    """Remove item from cart"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            # ✅ PRESERVED: Delete logic
            CartItem.objects.get(id=pk).delete()
            return Response({"message": "Removed"}, status=status.HTTP_200_OK)

        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# ALTERNATIVE: Combined Cart View (Optional)
# =========================
class CartView(GenericAPIView):
    """
    Combined cart view for all operations
    GET: Get cart
    POST: Add to cart
    PUT: Update cart item
    DELETE: Remove from cart
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's cart"""
        try:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Add item to cart"""
        try:
            cart, _ = Cart.objects.get_or_create(user=request.user)

            product_id = request.data.get('product')
            quantity = int(request.data.get('quantity', 1))

            if not product_id:
                return Response({"error": "Product ID missing"}, status=status.HTTP_400_BAD_REQUEST)

            product = Product.objects.filter(id=product_id).first()

            if not product:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product
            )

            if not created:
                item.quantity += quantity
            else:
                item.quantity = quantity

            item.save()

            return Response({"message": "Item added successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        """Update cart item quantity"""
        try:
            item_id = request.data.get('item_id')
            quantity = int(request.data.get('quantity', 1))

            item = CartItem.objects.get(id=item_id)

            if quantity <= 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()

            return Response({"message": "Updated"}, status=status.HTTP_200_OK)

        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """Remove item from cart"""
        try:
            CartItem.objects.get(id=pk).delete()
            return Response({"message": "Removed"}, status=status.HTTP_200_OK)

        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

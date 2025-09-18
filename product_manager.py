import json
import os
from typing import List, Dict, Optional

class ProductManager:
    def __init__(self, products_file: str = "new_products.json"):
        self.products_file = products_file
        self.products = self.load_products()
    
    def load_products(self) -> List[Dict]:
        """제품 데이터를 JSON 파일에서 로드"""
        try:
            if os.path.exists(self.products_file):
                with open(self.products_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.common_subscription_benefits = data.get('common_subscription_benefits', [])
                    self.common_purchase_benefits = data.get('common_purchase_benefits', [])
                    self.subscription_service_info = data.get('subscription_service_info', {})
                    return data.get('products', [])
            else:
                self.common_subscription_benefits = []
                self.common_purchase_benefits = []
                self.subscription_service_info = {}
                return []
        except Exception as e:
            print(f"제품 데이터 로드 중 오류 발생: {e}")
            self.common_subscription_benefits = []
            self.common_purchase_benefits = []
            self.subscription_service_info = {}
            return []
    
    def save_products(self) -> bool:
        """제품 데이터를 JSON 파일에 저장"""
        try:
            data = {"products": self.products}
            with open(self.products_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"제품 데이터 저장 중 오류 발생: {e}")
            return False
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """ID로 제품 정보 조회"""
        for product in self.products:
            if product.get('id') == product_id:
                return product
        return None
    
    def get_product_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 제품 정보 조회"""
        for product in self.products:
            if product.get('name') == name:
                return product
        return None
    
    def get_all_products(self) -> List[Dict]:
        """모든 제품 정보 조회"""
        return self.products
    
    def add_product(self, product: Dict) -> bool:
        """새 제품 추가"""
        try:
            # ID 자동 할당
            if 'id' not in product:
                max_id = max([p.get('id', 0) for p in self.products], default=0)
                product['id'] = max_id + 1
            
            self.products.append(product)
            return self.save_products()
        except Exception as e:
            print(f"제품 추가 중 오류 발생: {e}")
            return False
    
    def update_product(self, product_id: int, updated_product: Dict) -> bool:
        """제품 정보 업데이트"""
        try:
            for i, product in enumerate(self.products):
                if product.get('id') == product_id:
                    updated_product['id'] = product_id
                    self.products[i] = updated_product
                    return self.save_products()
            return False
        except Exception as e:
            print(f"제품 업데이트 중 오류 발생: {e}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """제품 삭제"""
        try:
            self.products = [p for p in self.products if p.get('id') != product_id]
            return self.save_products()
        except Exception as e:
            print(f"제품 삭제 중 오류 발생: {e}")
            return False
    
    def get_purchase_arguments(self, product_id: int) -> List[str]:
        """구매 유도 논거 조회 (공통 + 제품별)"""
        product = self.get_product_by_id(product_id)
        if product:
            common_benefits = getattr(self, 'common_purchase_benefits', [])
            product_benefits = product.get('purchase_benefits', [])
            return common_benefits + product_benefits
        return getattr(self, 'common_purchase_benefits', [])
    
    def get_subscription_arguments(self, product_id: int) -> List[str]:
        """구독 유도 논거 조회 (공통 + 제품별)"""
        product = self.get_product_by_id(product_id)
        if product:
            common_benefits = getattr(self, 'common_subscription_benefits', [])
            product_benefits = product.get('subscription_benefits', [])
            return common_benefits + product_benefits
        return getattr(self, 'common_subscription_benefits', [])
    
    
    def get_common_subscription_benefits(self) -> List[str]:
        """공통 구독 혜택 조회"""
        return getattr(self, 'common_subscription_benefits', [])
    
    def get_common_purchase_benefits(self) -> List[str]:
        """공통 구매 혜택 조회"""
        return getattr(self, 'common_purchase_benefits', [])
    
    def get_subscription_service_info(self) -> Dict:
        """구독 서비스 정보 조회"""
        return getattr(self, 'subscription_service_info', {})
    
    def get_care_service_info(self, product_id: int) -> Optional[Dict]:
        """제품별 케어 서비스 정보 조회"""
        product = self.get_product_by_id(product_id)
        if product:
            return product.get('care_service', {})
        return None
    
    def get_contract_periods(self, product_id: int) -> List[str]:
        """제품별 계약 주기 조회"""
        product = self.get_product_by_id(product_id)
        if product:
            return product.get('contract_periods', [])
        return []

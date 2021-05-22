import test_class
import unittest
from factory import Creator

serializer = Creator.factory_method("json")
multiplication = test_class.Tester


class UnitTestsJson(unittest.TestCase):
    def test_counter(self):
        self.assertEqual(test_class.count_numbers(10, 20),
                         serializer.loads(serializer.dumps(test_class.count_numbers(10, 20))))

    def test_negative_counter(self):
        self.assertEqual(test_class.count_numbers(-231231, 20321313),
                         serializer.loads(serializer.dumps(test_class.count_numbers(-231231, 20321313))))

    def test_takeaway_numbers(self):
        self.assertEqual(test_class.takeaway_numbers(321312, 4533432),
                         serializer.loads(serializer.dumps(test_class.takeaway_numbers(321312, 4533432))))

    def test_takeaway_negative_numbers(self):
        self.assertEqual(test_class.takeaway_numbers(-2312313, -544645646),
                         serializer.loads(serializer.dumps(test_class.takeaway_numbers(-2312313, -544645646))))

    def test_multiplication(self):
        self.assertEqual(multiplication.multiply_method(multiplication),
                         serializer.loads(serializer.dumps(multiplication.multiply_method(multiplication))))

    def test_objects(self):
        serializer.dump(multiplication, "C:\\Users\\Алексей\\PycharmProjects\\Lab2\\data.json", False, 4)
        mul_obj = serializer.load("C:\\Users\\Алексей\\PycharmProjects\\Lab2\\data.json")
        self.assertEqual(mul_obj.multiply_method(mul_obj), multiplication.multiply_method(multiplication))

    def test_classes(self):
        serializer.dump(test_class.Tester, "C:\\Users\\Алексей\\PycharmProjects\\Lab2\\data.json", False, 4)
        type_obj = type(multiplication)
        type_class = type(serializer.load("C:\\Users\\Алексей\\PycharmProjects\\Lab2\\data.json"))
        self.assertEqual(type_obj, type_class)
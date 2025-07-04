// lib/models/vehicle.dart
import 'dart:convert';

class Vehicle {
  final String plate;
  final String model;

  Vehicle({required this.plate, required this.model});

  factory Vehicle.fromMap(Map<String, dynamic> map) {
    return Vehicle(
      plate: map['plate'],
      model: map['model'],
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'plate': plate,
      'model': model,
    };
  }

  factory Vehicle.fromJson(String jsonString) {
    final map = Map<String, dynamic>.from(jsonDecode(jsonString));
    return Vehicle.fromMap(map);
  }

  String toJson() {
    return jsonEncode(toMap());
  }
}

import 'package:flutter/material.dart';
import '../models/vehicle.dart';

class AddVehicleScreen extends StatefulWidget {
  final Function(Vehicle) onAdd;

  AddVehicleScreen({required this.onAdd});

  @override
  _AddVehicleScreenState createState() => _AddVehicleScreenState();
}

class _AddVehicleScreenState extends State<AddVehicleScreen> {
  final _plateController = TextEditingController();
  final _modelController = TextEditingController();

  void _submit() {
    if (_plateController.text.isEmpty || _modelController.text.isEmpty) return;

    final vehicle = Vehicle(
      plate: _plateController.text.trim(),
      model: _modelController.text.trim(),
    );

    widget.onAdd(vehicle);
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Add Vehicle')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _plateController,
              decoration: InputDecoration(labelText: 'Plate Number'),
            ),
            TextField(
              controller: _modelController,
              decoration: InputDecoration(labelText: 'Car Model'),
            ),
            SizedBox(height: 20),
            ElevatedButton(onPressed: _submit, child: Text('Add')),
          ],
        ),
      ),
    );
  }
}

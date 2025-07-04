import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'models/vehicle.dart';
import 'screens/add_vehicle.dart';
import 'screens/home_screen.dart';
import 'screens/settings_screen.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'utils/notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService.init(); // Initialize notifications
  tz.initializeTimeZones();

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key); // Add key to constructor

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Driver Monitoring',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: Colors.grey[100],
      ),
      home: const VehicleSelectionScreen(),
    );
  }
}

class VehicleSelectionScreen extends StatefulWidget {
  const VehicleSelectionScreen({Key? key}) : super(key: key); // Add key

  @override
  _VehicleSelectionScreenState createState() => _VehicleSelectionScreenState();
}

class _VehicleSelectionScreenState extends State<VehicleSelectionScreen> {
  List<Vehicle> vehicles = [];

  @override
  void initState() {
    super.initState();
    loadVehicles();
  }

  Future<void> loadVehicles() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    final saved = prefs.getStringList('vehicles') ?? [];
    setState(() {
      vehicles = saved.map((v) => Vehicle.fromJson(v)).toList();
    });
  }

  Future<void> deleteVehicle(int index) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      vehicles.removeAt(index);
    });
    await prefs.setStringList('vehicles', vehicles.map((v) => v.toJson()).toList());
  }

  Future<void> addNewVehicle() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => AddVehicleScreen(
          onAdd: (Vehicle newVehicle) async {
            setState(() {
              vehicles.add(newVehicle);
            });
            SharedPreferences prefs = await SharedPreferences.getInstance();
            await prefs.setStringList('vehicles', vehicles.map((v) => v.toJson()).toList());
          },
        ),
      ),
    );
  }

  void onVehicleSelected(Vehicle vehicle) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => HomeScreen(vehicle: vehicle),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("اختر العربية"),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => SettingsScreen()),
              );
            },
          )
        ],
      ),
      body: vehicles.isEmpty
          ? const Center(child: Text("🚗 لم تتم إضافة أي عربيات بعد."))
          : ListView.builder(
        itemCount: vehicles.length,
        itemBuilder: (context, index) {
          final vehicle = vehicles[index];
          return Card(
            margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: const Icon(Icons.directions_car, color: Colors.blue),
              title: Text(vehicle.model, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text(vehicle.plate),
              onTap: () => onVehicleSelected(vehicle),
              trailing: IconButton(
                icon: const Icon(Icons.delete, color: Colors.red),
                onPressed: () => deleteVehicle(index),
              ),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: addNewVehicle,
        child: const Icon(Icons.add),
        tooltip: 'Add Vehicle',
      ),
    );
  }
}

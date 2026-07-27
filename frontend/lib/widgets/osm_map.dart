import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class OpenStreetMapView extends StatefulWidget {
  final LatLng initialLocation;
  final LatLng restrictedAreaCenter;
  final LatLngBounds allowedBounds;
  final double radius;
  final ValueChanged<LatLng> onLocationSelected;
  final MapController mapController;

  const OpenStreetMapView({
    super.key,
    required this.initialLocation,
    required this.restrictedAreaCenter,
    required this.allowedBounds,
    required this.radius,
    required this.onLocationSelected,
    required this.mapController,
  });

  @override
  State<OpenStreetMapView> createState() => _OpenStreetMapViewState();
}

class _OpenStreetMapViewState extends State<OpenStreetMapView> {
  late LatLng _selectedLocation;

  @override
  void initState() {
    super.initState();
    _selectedLocation = widget.initialLocation;
  }

  @override
  void didUpdateWidget(covariant OpenStreetMapView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialLocation != widget.initialLocation) {
      _selectedLocation = widget.initialLocation;
    }
  }

  @override
  Widget build(BuildContext context) {
    return FlutterMap(
      mapController: widget.mapController,
      options: MapOptions(
        initialCenter: widget.initialLocation,
        initialZoom: 16.0,
        onTap: (tapPosition, point) {
          setState(() {
            _selectedLocation = point;
          });
          widget.onLocationSelected(point);
        },
      ),
      children: [
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'com.startsmart.app',
        ),
        CircleLayer(
          circles: [
            CircleMarker(
              point: widget.restrictedAreaCenter,
              radius: 750,
              useRadiusInMeter: true,
              color: Colors.green.withOpacity(0.05),
              borderColor: Colors.green.withOpacity(0.35),
              borderStrokeWidth: 2,
            ),
            CircleMarker(
              point: _selectedLocation,
              radius: widget.radius,
              useRadiusInMeter: true,
              color: const Color(0xFF1E40AF).withOpacity(0.15),
              borderColor: const Color(0xFF1E40AF),
              borderStrokeWidth: 2,
            ),
          ],
        ),
        MarkerLayer(
          markers: [
            Marker(
              point: _selectedLocation,
              width: 48,
              height: 48,
              child: const Icon(
                Icons.location_pin,
                color: Color(0xFF1E40AF),
                size: 36,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

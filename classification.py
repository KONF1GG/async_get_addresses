from sklearn.neighbors import LocalOutlierFactor
import numpy as np
import functions

def convert_coordinates(coords):
    """ Convert coordinates to a numpy array. """
    return np.array([[float(coord[0]), float(coord[1])] for coord in coords])

# Test string to fetch areas
test = 'краснодарский , краснодар , ленина'

# Fetching areas using a function
areas = functions.get_areas(test)

coords = []

# Process each area
for area in areas:
    location = area.location
    if isinstance(location[0], str):
        # Convert to list of floats if necessary
        location = list(map(float, location))
    coords.extend([location])

# Debugging: Print the shape and content of coords
print("Coords:", coords)
print("Length of coords:", len(coords))

# Check for consistent lengths
for i, item in enumerate(coords):
    if len(item) != 2:
        print(f"Inconsistent length found in element {i}: {item}")

# Convert to numpy array
try:
    coordinates = np.array(coords)
except Exception as e:
    print("Error converting to numpy array:", e)
    raise

# Print the shape of the coordinates array
print("Shape of coordinates:", coordinates.shape)

print(len(areas)-100)
# Apply LocalOutlierFactor
lof = LocalOutlierFactor(n_neighbors=len(areas)-100)
y_pred = lof.fit_predict(coordinates)

# Extract outliers
for i, value in enumerate(coordinates[y_pred == -1]):
    print(i, value)

print("Выбросы:")
# print(outliers)

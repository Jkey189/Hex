CXX = clang++
CXXFLAGS = -std=c++17 -O3 -Wall -shared -fPIC -undefined dynamic_lookup
PYTHON_INCLUDES = $(shell python3 -m pybind11 --includes)
EXTENSION_SUFFIX = $(shell python3-config --extension-suffix)

TARGET = hex_cpp$(EXTENSION_SUFFIX)
SOURCE = alpha-beta-pruning.cpp

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) $(PYTHON_INCLUDES) $(SOURCE) -o $(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all clean
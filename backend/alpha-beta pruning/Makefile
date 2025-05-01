CXX = clang++
CXXFLAGS = -std=c++17 -O3 -Wall -shared -fPIC
PYTHON_INCLUDES = $(shell python3 -m pybind11 --includes)
EXTENSION_SUFFIX = $(shell python3-config --extension-suffix)
PYTHON_LDFLAGS = $(shell python3-config --ldflags)

TARGET = hex_cpp$(EXTENSION_SUFFIX)

all: $(TARGET)

$(TARGET): alpha-beta-pruning.cpp
	$(CXX) $(CXXFLAGS) $(PYTHON_INCLUDES) $(PYTHON_LDFLAGS) alpha-beta-pruning.cpp -o $(TARGET)

clean:
	rm -f $(TARGET) *.o

install: $(TARGET)
	cp $(TARGET) ..

.PHONY: all clean install
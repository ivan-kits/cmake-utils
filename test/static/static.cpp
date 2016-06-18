#ifndef SHARED_HPP
#define SHARED_HPP

#include "static.hpp"
#include <string>

Static::Static() : str("This is a C++ string from a static library.") {}

std::string
Static::GetString() {
	return str;
}

#endif

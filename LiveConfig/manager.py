import logging
from liveconfig.typechecker import TypeChecker

logger = logging.getLogger(__name__)

class LiveManager:
    def __init__(self):
        self.live_classes = {}
        self.live_instances = {}
        self.file_handler = None
    
    def register_class(self, cls):
        """
        Register a class to be tracked
        """
        self.live_classes[cls.__name__] = cls
        return cls
    
    def register_instance(self, name, instance):
        """
        Register an instance of a class to be tracked
        """
        if name in self.live_instances:
            raise ValueError(f"Instance with name {name} already exists.")
        
        # Load value from file if it exists, else use the default value
        if self.file_handler is not None and self.file_handler.loaded_values is not None and "live_instances" in self.file_handler.loaded_values:
            saved_attrs = self.file_handler.loaded_values["live_instances"].get(name, {})
            instance = self.load_values_into_instance(instance, saved_attrs)
        
        self.live_instances[name] = instance
        # Register the instance in its class if it has a _instances attribute
        cls = type(instance)
        if hasattr(cls, "_instances"):
            cls._instances.append(instance)
        else:
            cls._instances = [instance]

    def load_values_into_instance(self, instance, attrs):
        """
        Loads the values from the save file into the instance.
        """
        for attr, value in attrs.items():
            setattr(instance, attr, value)
        return instance
    
    def get_live_classes(self):
        """
        Get all live classes
        """
        return self.live_classes
    
    def get_live_class_by_name(self, class_name):
        """
        Get a live class by name
        """
        return self.live_classes.get(class_name)
    
    def get_live_instances(self, class_name):
        """
        Get all instances of a live class
        """
        cls = self.get_live_class_by_name(class_name)
        if cls:
            return getattr(cls, "_instances", [])
        return None
    
    def get_live_instance_by_name(self, instance_name):
        """
        Get a live class instance by name
        """
        if instance_name in self.live_instances:
            return self.live_instances[instance_name]
        else:
            logger.warning(f"WARNING: Instance '{instance_name}' does not exist")
            return None
        
    def get_live_instance_attr_by_name(self, instance, attr_name):
        """
        Get an attribute of a live instance by name
        """
        if instance is not None:
            attr = getattr(instance, attr_name, None)
            if attr is None:
                logger.warning(f"WARNING: Attribute '{attr_name}' does not exist on '{instance}'")
            return attr
        
    
    def set_live_instance_attr_by_name(self, instance_name, attr_name, value):
        instance = self.get_live_instance_by_name(instance_name)
        if instance is None: return None
        attr = self.get_live_instance_attr_by_name(instance, attr_name)
        if attr is None: return None
        
        if instance is not None:
            attr_type = type(getattr(instance, attr_name))
            if attr_type == bool:
                value = TypeChecker.handle_bool(value)
            elif attr_type == int:
                value = TypeChecker.handle_int(value)
            elif attr_type == tuple:
                value = TypeChecker.handle_tuple(value, instance, attr_name)
                if value is None:
                    return None
            elif attr_type == list:
                value = TypeChecker.handle_list(value, instance, attr_name)
                if value is None:
                    return None
            try:
                value = attr_type(value)
                return setattr(instance, attr_name, value)
            except Exception as e:
                logger.warning(f"WARNING: Failed to update: {e}")
                return None
        return None
    

    
    
    def serialize_instances(self):
        """
        This member function serializes the live instances to be saved.
        It removes any attributes that are not created by the user.
        """
        instances = self.live_instances
        serialized_instances = {}
        serialized_instances["live_instances"] = {}
        for instance_name, live_instance in instances.items():
            attributes = vars(live_instance)
            clean_attrs = {}
            for attr, value in attributes.items():
                if attr.startswith("__") or attr.startswith("_tracked_attrs"):
                    continue
                try:
                    clean_attrs[attr] = value
                except (TypeError, ValueError):
                    clean_attrs[attr] = str(value)

            serialized_instances["live_instances"][instance_name] = clean_attrs
        return serialized_instances
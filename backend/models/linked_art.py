"""
Linked Art Models - JSON-LD Data Structures
Pydantic models following the Linked Art specification for cultural heritage data
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime


# Base Linked Art Types

class LinkedArtEntity(BaseModel):
    """Base class for all Linked Art entities"""
    id: Optional[str] = Field(default=None, description="URI identifier")
    type: str = Field(description="Class type")
    _label: Optional[str] = Field(default=None, description="Human-readable label")


# Core Entity Types

class Identifier(LinkedArtEntity):
    """Identifier for an entity"""
    type: Literal["Identifier"] = "Identifier"
    content: str = Field(description="The identifier string")
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)


class Name(LinkedArtEntity):
    """Name of an entity"""
    type: Literal["Name"] = "Name"
    content: str = Field(description="The name string")
    language: Optional[List[LinkedArtEntity]] = Field(default=None)
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)


class Dimension(LinkedArtEntity):
    """Physical dimension measurement"""
    type: Literal["Dimension"] = "Dimension"
    value: float = Field(description="Numeric value")
    unit: LinkedArtEntity = Field(description="Unit of measurement")
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)


class TimeSpan(LinkedArtEntity):
    """Temporal extent"""
    type: Literal["TimeSpan"] = "TimeSpan"
    begin_of_the_begin: Optional[str] = Field(default=None, description="Earliest possible start")
    end_of_the_end: Optional[str] = Field(default=None, description="Latest possible end")
    identified_by: List[Union[Name, Identifier]] = Field(default_factory=list)


class Place(LinkedArtEntity):
    """Geographic location"""
    type: Literal["Place"] = "Place"
    identified_by: List[Union[Name, Identifier]] = Field(default_factory=list)
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)
    part_of: Optional[List['Place']] = Field(default=None)
    defined_by: Optional[str] = Field(default=None, description="WKT geometry")


class LinguisticObject(LinkedArtEntity):
    """Textual content"""
    type: Literal["LinguisticObject"] = "LinguisticObject"
    content: str = Field(description="The text content")
    language: Optional[List[LinkedArtEntity]] = Field(default=None)
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)


class VisualItem(LinkedArtEntity):
    """Visual representation"""
    type: Literal["VisualItem"] = "VisualItem"
    digitally_shown_by: Optional[List[LinkedArtEntity]] = Field(default=None)
    represents: Optional[List[LinkedArtEntity]] = Field(default=None)


class DigitalObject(LinkedArtEntity):
    """Digital representation"""
    type: Literal["DigitalObject"] = "DigitalObject"
    access_point: Optional[List[LinkedArtEntity]] = Field(default=None)
    format: Optional[str] = Field(default=None)
    conforms_to: Optional[List[LinkedArtEntity]] = Field(default=None)


# Person and Group

class Person(LinkedArtEntity):
    """Individual person"""
    type: Literal["Person"] = "Person"
    identified_by: List[Union[Name, Identifier]] = Field(default_factory=list)
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)
    born: Optional[LinkedArtEntity] = Field(default=None, description="Birth event")
    died: Optional[LinkedArtEntity] = Field(default=None, description="Death event")
    nationality: Optional[List[LinkedArtEntity]] = Field(default=None)
    residence: Optional[List[Place]] = Field(default=None)
    member_of: Optional[List[LinkedArtEntity]] = Field(default=None)
    influenced_by: Optional[List['Person']] = Field(default=None)


class Group(LinkedArtEntity):
    """Organization or collective"""
    type: Literal["Group"] = "Group"
    identified_by: List[Union[Name, Identifier]] = Field(default_factory=list)
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)
    formed_by: Optional[LinkedArtEntity] = Field(default=None)
    dissolved_by: Optional[LinkedArtEntity] = Field(default=None)


# Activities and Events

class Activity(LinkedArtEntity):
    """Generic activity"""
    type: str = Field(default="Activity")
    carried_out_by: Optional[List[Union[Person, Group]]] = Field(default=None)
    took_place_at: Optional[List[Place]] = Field(default=None)
    timespan: Optional[TimeSpan] = Field(default=None)
    technique: Optional[List[LinkedArtEntity]] = Field(default=None)
    used_specific_object: Optional[List[LinkedArtEntity]] = Field(default=None)


class Production(Activity):
    """Creation/production activity"""
    type: Literal["Production"] = "Production"
    produced: Optional[LinkedArtEntity] = Field(default=None)


class Acquisition(Activity):
    """Acquisition activity"""
    type: Literal["Acquisition"] = "Acquisition"
    transferred_title_of: Optional[List[LinkedArtEntity]] = Field(default=None)
    transferred_title_from: Optional[List[Union[Person, Group]]] = Field(default=None)
    transferred_title_to: Optional[List[Union[Person, Group]]] = Field(default=None)


# Primary Object Types

class HumanMadeObject(LinkedArtEntity):
    """Physical object created by humans (artwork)"""
    type: Literal["HumanMadeObject"] = "HumanMadeObject"

    # Identification
    identified_by: List[Union[Name, Identifier]] = Field(default_factory=list)
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)

    # Descriptive information
    referred_to_by: List[LinguisticObject] = Field(default_factory=list)

    # Physical characteristics
    made_of: List[LinkedArtEntity] = Field(default_factory=list, description="Materials")
    dimension: List[Dimension] = Field(default_factory=list)

    # Production
    produced_by: Optional[Production] = Field(default=None)

    # Current state
    current_owner: Optional[List[Union[Person, Group]]] = Field(default=None)
    current_location: Optional[Place] = Field(default=None)
    current_keeper: Optional[List[Union[Person, Group]]] = Field(default=None)

    # Provenance
    changed_ownership_through: List[Acquisition] = Field(default_factory=list)

    # Subject matter
    shows: Optional[List[VisualItem]] = Field(default=None)
    about: Optional[List[LinkedArtEntity]] = Field(default=None)

    # Parts and members
    part_of: Optional[List['HumanMadeObject']] = Field(default=None)
    member_of: Optional[List[LinkedArtEntity]] = Field(default=None)

    # Digital representations
    representation: Optional[List[VisualItem]] = Field(default=None)
    subject_of: Optional[List[LinguisticObject]] = Field(default=None)


class Set(LinkedArtEntity):
    """Conceptual set or collection"""
    type: Literal["Set"] = "Set"
    identified_by: List[Union[Name, Identifier]] = Field(default_factory=list)
    classified_as: List[LinkedArtEntity] = Field(default_factory=list)
    member_of: Optional[List['Set']] = Field(default=None)
    members: Optional[List[LinkedArtEntity]] = Field(default=None)


# Activity Streams (for search results)

class OrderedCollectionPage(BaseModel):
    """Activity Streams OrderedCollectionPage"""
    context: str = Field(alias="@context", default="https://www.w3.org/ns/activitystreams")
    id: str
    type: Literal["OrderedCollectionPage"] = "OrderedCollectionPage"
    partOf: Optional[Dict[str, Any]] = Field(default=None)
    orderedItems: List[Dict[str, Any]] = Field(default_factory=list)
    startIndex: Optional[int] = Field(default=None)
    next: Optional[str] = Field(default=None)
    prev: Optional[str] = Field(default=None)


# Utility Functions

def create_identifier(content: str, id_type: Optional[str] = None) -> Identifier:
    """Helper to create an Identifier"""
    identifier = Identifier(content=content)
    if id_type:
        identifier.classified_as = [
            LinkedArtEntity(type="Type", _label=id_type)
        ]
    return identifier


def create_name(content: str, name_type: Optional[str] = "Primary Name") -> Name:
    """Helper to create a Name"""
    name = Name(content=content)
    if name_type:
        name.classified_as = [
            LinkedArtEntity(type="Type", _label=name_type)
        ]
    return name


def create_dimension(value: float, unit: str, dimension_type: str) -> Dimension:
    """Helper to create a Dimension"""
    return Dimension(
        value=value,
        unit=LinkedArtEntity(type="MeasurementUnit", _label=unit),
        classified_as=[LinkedArtEntity(type="Type", _label=dimension_type)]
    )


def create_timespan(begin: Optional[str] = None, end: Optional[str] = None, label: Optional[str] = None) -> TimeSpan:
    """Helper to create a TimeSpan"""
    timespan = TimeSpan(
        begin_of_the_begin=begin,
        end_of_the_end=end
    )
    if label:
        timespan.identified_by = [create_name(label)]
    return timespan


# Model updates for forward references
Place.model_rebuild()
Person.model_rebuild()
HumanMadeObject.model_rebuild()
Set.model_rebuild()


__all__ = [
    'LinkedArtEntity',
    'Identifier',
    'Name',
    'Dimension',
    'TimeSpan',
    'Place',
    'LinguisticObject',
    'VisualItem',
    'DigitalObject',
    'Person',
    'Group',
    'Activity',
    'Production',
    'Acquisition',
    'HumanMadeObject',
    'Set',
    'OrderedCollectionPage',
    'create_identifier',
    'create_name',
    'create_dimension',
    'create_timespan'
]

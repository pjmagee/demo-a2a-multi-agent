from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.api_client_builder import enable_backing_store_for_serialization_writer_factory, register_default_deserializer, register_default_serializer
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from kiota_abstractions.serialization import ParseNodeFactoryRegistry, SerializationWriterFactoryRegistry
from kiota_serialization_form.form_parse_node_factory import FormParseNodeFactory
from kiota_serialization_form.form_serialization_writer_factory import FormSerializationWriterFactory
from kiota_serialization_json.json_parse_node_factory import JsonParseNodeFactory
from kiota_serialization_json.json_serialization_writer_factory import JsonSerializationWriterFactory
from kiota_serialization_multipart.multipart_serialization_writer_factory import MultipartSerializationWriterFactory
from kiota_serialization_text.text_parse_node_factory import TextParseNodeFactory
from kiota_serialization_text.text_serialization_writer_factory import TextSerializationWriterFactory
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .creators.creators_request_builder import CreatorsRequestBuilder
    from .creator_roles.creator_roles_request_builder import CreatorRolesRequestBuilder
    from .developers.developers_request_builder import DevelopersRequestBuilder
    from .games.games_request_builder import GamesRequestBuilder
    from .genres.genres_request_builder import GenresRequestBuilder
    from .platforms.platforms_request_builder import PlatformsRequestBuilder
    from .publishers.publishers_request_builder import PublishersRequestBuilder
    from .stores.stores_request_builder import StoresRequestBuilder
    from .tags.tags_request_builder import TagsRequestBuilder

class RawgClient(BaseRequestBuilder):
    """
    The main entry point of the SDK, exposes the configuration and the fluent API.
    """
    def __init__(self,request_adapter: RequestAdapter) -> None:
        """
        Instantiates a new RawgClient and sets the default values.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        if request_adapter is None:
            raise TypeError("request_adapter cannot be null.")
        super().__init__(request_adapter, "{+baseurl}", None)
        register_default_serializer(JsonSerializationWriterFactory)
        register_default_serializer(TextSerializationWriterFactory)
        register_default_serializer(FormSerializationWriterFactory)
        register_default_serializer(MultipartSerializationWriterFactory)
        register_default_deserializer(JsonParseNodeFactory)
        register_default_deserializer(TextParseNodeFactory)
        register_default_deserializer(FormParseNodeFactory)
        if not self.request_adapter.base_url:
            self.request_adapter.base_url = "https://api.rawg.io/api"
        self.path_parameters["base_url"] = self.request_adapter.base_url
    
    @property
    def creator_roles(self) -> CreatorRolesRequestBuilder:
        """
        The creatorRoles property
        """
        from .creator_roles.creator_roles_request_builder import CreatorRolesRequestBuilder

        return CreatorRolesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def creators(self) -> CreatorsRequestBuilder:
        """
        The creators property
        """
        from .creators.creators_request_builder import CreatorsRequestBuilder

        return CreatorsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def developers(self) -> DevelopersRequestBuilder:
        """
        The developers property
        """
        from .developers.developers_request_builder import DevelopersRequestBuilder

        return DevelopersRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def games(self) -> GamesRequestBuilder:
        """
        The games property
        """
        from .games.games_request_builder import GamesRequestBuilder

        return GamesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def genres(self) -> GenresRequestBuilder:
        """
        The genres property
        """
        from .genres.genres_request_builder import GenresRequestBuilder

        return GenresRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def platforms(self) -> PlatformsRequestBuilder:
        """
        The platforms property
        """
        from .platforms.platforms_request_builder import PlatformsRequestBuilder

        return PlatformsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def publishers(self) -> PublishersRequestBuilder:
        """
        The publishers property
        """
        from .publishers.publishers_request_builder import PublishersRequestBuilder

        return PublishersRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def stores(self) -> StoresRequestBuilder:
        """
        The stores property
        """
        from .stores.stores_request_builder import StoresRequestBuilder

        return StoresRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def tags(self) -> TagsRequestBuilder:
        """
        The tags property
        """
        from .tags.tags_request_builder import TagsRequestBuilder

        return TagsRequestBuilder(self.request_adapter, self.path_parameters)
    


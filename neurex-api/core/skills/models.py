from sqlmodel import Field, SQLModel


class PluginHubItem(SQLModel, table=True):
    id: str = Field(primary_key=True, description="The unique identifier for the plugin (e.g. username-pluginname)")
    name: str = Field(..., description="The display name of the plugin")
    description: str = Field(..., description="A short description of the plugin's capabilities")
    url: str = Field(..., description="The Git repository URL")
    author: str = Field(..., description="The author's name or handle")
    version: str = Field(..., description="Version string")
    category: str = Field("All", description="Marketplace category")
    plugin_type: str = Field("skill", description="Either 'skill' or 'mcp'")
    is_official: bool = Field(False, description="Whether this is an official curated plugin")
    stars: int = Field(0, description="Number of stars/upvotes")
    enabled: bool = Field(True, description="Whether the plugin is enabled in the hub")
    published_at: float = Field(..., description="Unix timestamp of when the plugin was published")

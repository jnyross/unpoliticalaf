"""Strict forbidden-import contracts for independently landing optional modules."""

# Only this developer adapter consumes the architecture tool, not production.
from importlinter import Contract, fields  # deptry: ignore[DEP004]
from importlinter.contracts.forbidden import ForbiddenContract  # deptry: ignore[DEP004]


class OptionalModulesForbiddenContract(Contract):
    """Activate exact permissions only once their optional module exists.

    Existing-module permissions still have to match a real import. Optional
    modules join the source set too, so they cannot hide upward dependencies.
    """

    optional_modules = fields.SetField(subfield=fields.ModuleField(), required=False)
    optional_imports = fields.SetField(subfield=fields.ImportExpressionField(), required=False)

    def check(self, graph, verbose):
        optional_names = {module.name for module in self.optional_modules or ()}
        optional_imports = self.optional_imports or ()
        for edge in optional_imports:
            if edge.has_wildcard_expression() or edge.imported.expression not in optional_names:
                raise ValueError("Optional imports must name an exact declared optional module")

        # Delegate matching, transitive checks, stale permissions and reporting
        # to the pinned standard contract rather than duplicating its logic.
        self._forbidden = ForbiddenContract(
            self.name,
            self.session_options,
            self.contract_options,
        )
        self._forbidden.source_modules |= {
            fields.ModuleExpressionField().parse(name)
            for name in optional_names
            if name in graph.modules
        }
        self._forbidden.ignore_imports = set(self._forbidden.ignore_imports or ()) | {
            edge for edge in optional_imports if edge.imported.expression in graph.modules
        }
        return self._forbidden.check(graph, verbose)

    def render_broken_contract(self, check):
        self._forbidden.render_broken_contract(check)

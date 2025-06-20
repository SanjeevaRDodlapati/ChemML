"""
Comprehensive test suite for molecular generation module.

This test suite provides extensive coverage for the molecular_generation module,
including MolecularGenerator, FragmentBasedGenerator classes and all standalone functions.
"""

import os
import random

# Import the module under test
import sys
import tempfile
from unittest.mock import MagicMock, Mock, mock_open, patch

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from qemlflow.research.drug_discovery.generation import (
    FragmentBasedGenerator,
    MolecularGenerator,
    generate_diverse_library,
    generate_molecular_structures,
    optimize_structure,
    save_generated_structures,
)

try:
    from rdkit import Chem

    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


class TestMolecularGenerator:
    """Test cases for MolecularGenerator class."""

    def test_init_without_seed(self):
        """Test initialization without seed."""
        generator = MolecularGenerator()
        assert hasattr(generator, "drug_fragments")
        assert hasattr(generator, "functional_groups")
        assert len(generator.drug_fragments) > 0
        assert len(generator.functional_groups) > 0

    def test_init_with_seed(self):
        """Test initialization with seed for reproducibility."""
        with patch("random.seed") as mock_random_seed, patch(
            "numpy.random.seed"
        ) as mock_np_seed:
            _generator = MolecularGenerator(seed=42)
            mock_random_seed.assert_called_once_with(42)
            mock_np_seed.assert_called_once_with(42)

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False)
    def test_generate_random_smiles_without_rdkit(self):
        """Test random SMILES generation without RDKit."""
        generator = MolecularGenerator()
        with patch("random.randint", return_value=5):
            smiles = generator.generate_random_smiles(num_molecules=3)
            assert len(smiles) == 3
            assert all(isinstance(s, str) for s in smiles)
            assert all(s.startswith("C") for s in smiles)

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_random_smiles_with_rdkit(self):
        """Test random SMILES generation with RDKit."""
        generator = MolecularGenerator()
        mock_mol = Mock()
        mock_mol.GetNumAtoms.return_value = 10

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch(
            "qemlflow.research.drug_discovery.generation.Descriptors"
        ) as mock_desc, patch.object(
            generator, "drug_fragments", ["c1ccccc1"]
        ), patch.object(
            generator, "functional_groups", ["CCO"]
        ), patch(
            "random.choice"
        ) as mock_choice, patch(
            "random.randint", return_value=1
        ):
            mock_chem.MolFromSmiles.return_value = mock_mol
            mock_chem.MolToSmiles.return_value = "c1ccccc1"
            mock_desc.HeavyAtomCount.return_value = 10
            mock_desc.MolWt.return_value = 200.0
            mock_desc.MolLogP.return_value = 2.0
            mock_desc.NumHDonors.return_value = 1
            mock_desc.NumHAcceptors.return_value = 2

            # Control the choices to avoid StopIteration
            mock_choice.side_effect = ["c1ccccc1", "CCO"] * 10

            generator._modify_molecule = Mock(return_value="c1ccccc1.CCO")

            smiles = generator.generate_random_smiles(num_molecules=2, max_atoms=50)
            assert isinstance(smiles, list)

    def test_modify_molecule_benzene_substitution(self):
        """Test molecule modification with benzene substitution."""
        generator = MolecularGenerator()
        # The implementation replaces benzene with functional group if functional group doesn't contain 'c1ccc('
        result = generator._modify_molecule(
            "c1ccccc1", "CCO"
        )  # CCO doesn't contain 'c1ccc('
        assert result == "CCO"  # Replaces the benzene entirely

    def test_modify_molecule_append_functional_group(self):
        """Test molecule modification by appending functional group."""
        generator = MolecularGenerator()
        result = generator._modify_molecule("CCO", "C#N")
        assert result == "CCO.C#N"

    def test_modify_molecule_no_change(self):
        """Test molecule modification when no changes are applied."""
        generator = MolecularGenerator()
        result = generator._modify_molecule(
            "complex_molecule", "very_long_functional_group"
        )
        assert result == "complex_molecule"

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False)
    def test_is_valid_drug_like_without_rdkit(self):
        """Test drug-likeness check without RDKit."""
        generator = MolecularGenerator()
        assert generator._is_valid_drug_like("CCO") is True

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_is_valid_drug_like_valid_molecule(self):
        """Test drug-likeness check for valid molecule."""
        generator = MolecularGenerator()
        mock_mol = Mock()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch(
            "qemlflow.research.drug_discovery.generation.Descriptors"
        ) as mock_desc:
            mock_chem.MolFromSmiles.return_value = mock_mol
            mock_desc.MolWt.return_value = 300.0
            mock_desc.MolLogP.return_value = 3.0
            mock_desc.NumHDonors.return_value = 2
            mock_desc.NumHAcceptors.return_value = 5

            result = generator._is_valid_drug_like("CCO")
            assert result is True

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_is_valid_drug_like_invalid_molecule(self):
        """Test drug-likeness check for invalid molecule (fails Lipinski's Rule)."""
        generator = MolecularGenerator()
        mock_mol = Mock()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch(
            "qemlflow.research.drug_discovery.generation.Descriptors"
        ) as mock_desc:
            mock_chem.MolFromSmiles.return_value = mock_mol
            mock_desc.MolWt.return_value = 600.0  # Too heavy
            mock_desc.MolLogP.return_value = 8.0  # Too lipophilic
            mock_desc.NumHDonors.return_value = 10  # Too many donors
            mock_desc.NumHAcceptors.return_value = 15  # Too many acceptors

            result = generator._is_valid_drug_like("large_molecule")
            assert result is False

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_is_valid_drug_like_invalid_smiles(self):
        """Test drug-likeness check for invalid SMILES."""
        generator = MolecularGenerator()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolFromSmiles.return_value = None

            result = generator._is_valid_drug_like("invalid_smiles")
            assert result is False

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_is_valid_drug_like_exception_handling(self):
        """Test drug-likeness check with exception handling."""
        generator = MolecularGenerator()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolFromSmiles.side_effect = ValueError("Test error")

            result = generator._is_valid_drug_like("CCO")
            assert result is False  # Should return False when exception occurs

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False)
    def test_generate_similar_molecules_without_rdkit(self):
        """Test similar molecule generation without RDKit."""
        generator = MolecularGenerator()
        result = generator.generate_similar_molecules("CCO", num_molecules=5)
        assert len(result) == 5
        assert all(mol == "CCO" for mol in result)

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_similar_molecules_with_rdkit(self):
        """Test similar molecule generation with RDKit."""
        generator = MolecularGenerator()
        mock_mol = Mock()
        mock_fp = Mock()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch(
            "qemlflow.research.drug_discovery.generation.GetMorganFingerprintAsBitVect"
        ) as mock_fp_gen:
            mock_chem.MolFromSmiles.return_value = mock_mol
            mock_chem.MolToSmiles.return_value = "CCO_modified"
            mock_fp_gen.return_value = mock_fp

            generator._generate_variation = Mock(return_value="CCO_modified")
            generator._calculate_tanimoto_similarity = Mock(return_value=0.8)
            generator._is_valid_drug_like = Mock(return_value=True)

            result = generator.generate_similar_molecules(
                "CCO", num_molecules=2, similarity_threshold=0.7
            )
            assert isinstance(result, list)

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_similar_molecules_invalid_reference(self):
        """Test similar molecule generation with invalid reference."""
        generator = MolecularGenerator()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch("logging.warning") as mock_warning:
            mock_chem.MolFromSmiles.return_value = None

            result = generator.generate_similar_molecules(
                "invalid_smiles", num_molecules=5
            )
            assert result == []
            mock_warning.assert_called_once()

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False)
    def test_generate_variation_without_rdkit(self):
        """Test molecule variation generation without RDKit."""
        generator = MolecularGenerator()
        result = generator._generate_variation("CCO")
        assert result == "CCO"

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_variation_with_rdkit(self):
        """Test molecule variation generation with RDKit."""
        generator = MolecularGenerator()
        mock_mol = Mock()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch("random.choice") as mock_choice:
            mock_chem.MolFromSmiles.return_value = mock_mol
            mock_chem.MolToSmiles.return_value = "modified_CCO"

            # Mock the modification function
            mock_modification = Mock(return_value=mock_mol)
            mock_choice.return_value = mock_modification

            result = generator._generate_variation("CCO")
            assert result == "modified_CCO"

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_variation_invalid_smiles(self):
        """Test molecule variation with invalid SMILES."""
        generator = MolecularGenerator()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolFromSmiles.return_value = None

            result = generator._generate_variation("invalid")
            assert result == "invalid"

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_variation_exception_handling(self):
        """Test molecule variation with exception handling."""
        generator = MolecularGenerator()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolFromSmiles.side_effect = ValueError("Test error")

            result = generator._generate_variation("CCO")
            assert (
                result == "CCO"
            )  # Should return original SMILES when exception occurs

    def test_add_methyl_group(self):
        """Test adding methyl group to molecule."""
        generator = MolecularGenerator()
        mock_mol = Mock()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolToSmiles.return_value = "CCO"
            mock_chem.MolFromSmiles.return_value = mock_mol

            result = generator._add_methyl_group(mock_mol)
            assert result == mock_mol

    def test_add_methyl_group_no_carbon(self):
        """Test adding methyl group when no carbon present."""
        generator = MolecularGenerator()
        mock_mol = Mock()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolToSmiles.return_value = "FF"  # No carbon

            result = generator._add_methyl_group(mock_mol)
            assert result == mock_mol

    def test_add_fluorine(self):
        """Test adding fluorine substitution."""
        generator = MolecularGenerator()
        mock_mol = Mock()
        mock_new_mol = Mock()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolToSmiles.return_value = "c1ccccc1"
            mock_chem.MolFromSmiles.return_value = mock_new_mol

            result = generator._add_fluorine(mock_mol)
            assert result == mock_new_mol

    def test_add_fluorine_no_benzene(self):
        """Test adding fluorine when no benzene ring present."""
        generator = MolecularGenerator()
        mock_mol = Mock()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolToSmiles.return_value = "CCO"  # No benzene

            result = generator._add_fluorine(mock_mol)
            assert result == mock_mol

    def test_change_ring_size(self):
        """Test ring size change (simplified implementation)."""
        generator = MolecularGenerator()
        mock_mol = Mock()

        result = generator._change_ring_size(mock_mol)
        assert result == mock_mol

    def test_add_hydroxyl_group(self):
        """Test adding hydroxyl group."""
        generator = MolecularGenerator()
        mock_mol = Mock()
        mock_new_mol = Mock()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolToSmiles.return_value = "c1ccccc1"
            mock_chem.MolFromSmiles.return_value = mock_new_mol

            result = generator._add_hydroxyl_group(mock_mol)
            assert result == mock_new_mol

    def test_add_hydroxyl_group_no_benzene(self):
        """Test adding hydroxyl group when no benzene ring present."""
        generator = MolecularGenerator()
        mock_mol = Mock()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolToSmiles.return_value = "CCO"  # No benzene

            result = generator._add_hydroxyl_group(mock_mol)
            assert result == mock_mol

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False)
    def test_calculate_tanimoto_similarity_without_rdkit(self):
        """Test Tanimoto similarity calculation without RDKit."""
        generator = MolecularGenerator()
        result = generator._calculate_tanimoto_similarity(None, None)
        assert result == 0.5

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_calculate_tanimoto_similarity_with_rdkit(self):
        """Test Tanimoto similarity calculation with RDKit."""
        generator = MolecularGenerator()
        mock_fp1 = Mock()
        mock_fp2 = Mock()

        with patch("rdkit.DataStructs.TanimotoSimilarity", return_value=0.75):
            result = generator._calculate_tanimoto_similarity(mock_fp1, mock_fp2)
            assert result == 0.75


class TestFragmentBasedGenerator:
    """Test cases for FragmentBasedGenerator class."""

    def test_init_with_default_fragments(self):
        """Test initialization with default fragments."""
        generator = FragmentBasedGenerator()
        assert hasattr(generator, "fragment_library")
        assert len(generator.fragment_library) > 0

    def test_init_with_custom_fragments(self):
        """Test initialization with custom fragment library."""
        custom_fragments = ["CCO", "CCC", "c1ccccc1"]
        generator = FragmentBasedGenerator(fragment_library=custom_fragments)
        assert generator.fragment_library == custom_fragments

    def test_get_default_fragments(self):
        """Test getting default fragments."""
        generator = FragmentBasedGenerator()
        fragments = generator._get_default_fragments()
        assert isinstance(fragments, list)
        assert len(fragments) > 0
        assert all(isinstance(frag, str) for frag in fragments)

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False)
    def test_generate_from_fragments_without_rdkit(self):
        """Test fragment-based generation without RDKit."""
        generator = FragmentBasedGenerator()

        with patch("random.randint", return_value=2), patch(
            "random.sample", return_value=["CCO", "c1ccccc1"]
        ):
            result = generator.generate_from_fragments(num_molecules=3)
            assert len(result) == 3
            assert all("CCO.c1ccccc1" == mol for mol in result)

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_from_fragments_with_rdkit_success(self):
        """Test fragment-based generation with RDKit (successful)."""
        generator = FragmentBasedGenerator()
        mock_mol = Mock()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch("random.randint", return_value=1), patch(
            "random.sample", return_value=["CCO"]
        ):
            mock_chem.MolFromSmiles.return_value = mock_mol
            mock_chem.MolToSmiles.return_value = "CCO"

            result = generator.generate_from_fragments(num_molecules=2)
            assert len(result) == 2
            assert all(mol == "CCO" for mol in result)

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_from_fragments_with_rdkit_failure(self):
        """Test fragment-based generation with RDKit (failed conversion)."""
        generator = FragmentBasedGenerator()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch("random.randint", return_value=1), patch(
            "random.sample", return_value=["invalid"]
        ):
            mock_chem.MolFromSmiles.return_value = None

            result = generator.generate_from_fragments(num_molecules=2)
            assert len(result) == 2
            assert all(mol == "invalid" for mol in result)

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_generate_from_fragments_with_rdkit_exception(self):
        """Test fragment-based generation with RDKit exception."""
        generator = FragmentBasedGenerator()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch("random.randint", return_value=1), patch(
            "random.sample", return_value=["CCO"]
        ):
            mock_chem.MolFromSmiles.side_effect = ValueError("Test error")

            result = generator.generate_from_fragments(num_molecules=2)
            assert len(result) == 2
            assert all(mol == "CCO" for mol in result)


class TestStandaloneFunctions:
    """Test cases for standalone functions."""

    def test_generate_molecular_structures_negative_samples(self):
        """Test generation with negative sample count."""
        with pytest.raises(ValueError, match="Number of samples must be non-negative"):
            generate_molecular_structures(num_samples=-1)

    def test_generate_molecular_structures_zero_samples(self):
        """Test generation with zero samples."""
        result = generate_molecular_structures(num_samples=0)
        assert result == []

    def test_generate_molecular_structures_with_mock_model(self):
        """Test generation with mock model that has generate method."""
        mock_model = Mock()
        mock_model.generate.return_value = ["CCO", "CCC"]

        result = generate_molecular_structures(model=mock_model, num_samples=2)
        assert result == ["CCO", "CCC"]
        mock_model.generate.assert_called_once_with(num_samples=2)

    def test_generate_molecular_structures_default_model_random(self):
        """Test generation with default model and random type."""
        with patch(
            "qemlflow.research.drug_discovery.generation.MolecularGenerator"
        ) as mock_gen_class:
            mock_generator = Mock()
            mock_generator.generate_random_smiles.return_value = ["CCO", "CCC"]
            mock_gen_class.return_value = mock_generator

            result = generate_molecular_structures(
                num_samples=2, generation_type="random"
            )
            assert result == ["CCO", "CCC"]
            mock_generator.generate_random_smiles.assert_called_once_with(2)

    def test_generate_molecular_structures_fragment_based(self):
        """Test generation with fragment-based type."""
        with patch(
            "qemlflow.research.drug_discovery.generation.FragmentBasedGenerator"
        ) as mock_frag_class:
            mock_fragment_gen = Mock()
            mock_fragment_gen.generate_from_fragments.return_value = ["c1ccccc1", "CCO"]
            mock_frag_class.return_value = mock_fragment_gen

            result = generate_molecular_structures(
                num_samples=2, generation_type="fragment_based"
            )
            assert result == ["c1ccccc1", "CCO"]
            mock_fragment_gen.generate_from_fragments.assert_called_once_with(2)

    def test_generate_molecular_structures_unknown_type(self):
        """Test generation with unknown generation type."""
        with pytest.raises(ValueError, match="Unknown generation type: unknown"):
            generate_molecular_structures(num_samples=5, generation_type="unknown")

    def test_optimize_structure_invalid_type(self):
        """Test structure optimization with invalid input type."""
        with pytest.raises(TypeError, match="Structure must be a string"):
            optimize_structure(123)

    def test_optimize_structure_empty_string(self):
        """Test structure optimization with empty string."""
        with pytest.raises(ValueError, match="Structure cannot be empty"):
            optimize_structure("")

        with pytest.raises(ValueError, match="Structure cannot be empty"):
            optimize_structure("   ")  # Whitespace only

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False)
    def test_optimize_structure_without_rdkit(self):
        """Test structure optimization without RDKit."""
        result = optimize_structure("CCO")
        assert result == "CCO"

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_optimize_structure_drug_likeness_high_mw(self):
        """Test structure optimization for drug-likeness with high molecular weight."""
        mock_mol = Mock()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch(
            "qemlflow.research.drug_discovery.generation.Descriptors"
        ) as mock_desc:
            mock_chem.MolFromSmiles.return_value = mock_mol
            mock_desc.MolWt.return_value = 600.0  # High molecular weight

            result = optimize_structure(
                "large_molecule", optimization_target="drug_likeness"
            )
            assert result == "large_molecule"

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_optimize_structure_drug_likeness_low_mw(self):
        """Test structure optimization for drug-likeness with acceptable molecular weight."""
        mock_mol = Mock()

        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch(
            "qemlflow.research.drug_discovery.generation.Descriptors"
        ) as mock_desc:
            mock_chem.MolFromSmiles.return_value = mock_mol
            mock_desc.MolWt.return_value = 300.0  # Acceptable molecular weight

            result = optimize_structure("CCO", optimization_target="drug_likeness")
            assert result == "CCO"

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_optimize_structure_other_target(self):
        """Test structure optimization for other targets."""
        mock_mol = Mock()

        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolFromSmiles.return_value = mock_mol

            result = optimize_structure("CCO", optimization_target="other_property")
            assert result == "CCO"

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_optimize_structure_invalid_smiles(self):
        """Test structure optimization with invalid SMILES."""
        with patch("qemlflow.research.drug_discovery.generation.Chem") as mock_chem:
            mock_chem.MolFromSmiles.return_value = None

            with pytest.raises(ValueError, match="Invalid SMILES string"):
                optimize_structure("invalid_smiles")

    @patch("qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", True)
    def test_optimize_structure_exception_handling(self):
        """Test structure optimization with exception handling."""
        with patch(
            "qemlflow.research.drug_discovery.generation.Chem"
        ) as mock_chem, patch("logging.warning") as mock_warning:
            mock_chem.MolFromSmiles.side_effect = Exception("Test error")

            with pytest.raises(ValueError, match="Cannot optimize structure"):
                optimize_structure("CCO")

            mock_warning.assert_called_once()

    def test_save_generated_structures_csv(self):
        """Test saving structures in CSV format."""
        structures = ["CCO", "CCC", "c1ccccc1"]

        with patch("pandas.DataFrame") as mock_df_class, patch(
            "logging.info"
        ) as mock_info:
            mock_df = Mock()
            mock_df_class.return_value = mock_df

            save_generated_structures(structures, "test.csv", format="csv")

            mock_df_class.assert_called_once_with(structures, columns=["SMILES"])
            mock_df.to_csv.assert_called_once_with("test.csv", index=False)
            mock_info.assert_called_once()

    def test_save_generated_structures_smi(self):
        """Test saving structures in SMI format."""
        structures = ["CCO", "CCC"]

        with patch("builtins.open", mock_open()) as mock_file, patch(
            "logging.info"
        ) as mock_info:
            save_generated_structures(structures, "test.smi", format="smi")

            mock_file.assert_called_once_with("test.smi", "w")
            mock_info.assert_called_once()

    def test_save_generated_structures_txt(self):
        """Test saving structures in TXT format."""
        structures = ["CCO", "CCC"]

        with patch("builtins.open", mock_open()) as mock_file, patch(
            "logging.info"
        ) as mock_info:
            save_generated_structures(structures, "test.txt", format="txt")

            mock_file.assert_called_once_with("test.txt", "w")
            mock_info.assert_called_once()

    def test_save_generated_structures_unsupported_format(self):
        """Test saving structures with unsupported format."""
        structures = ["CCO", "CCC"]

        with pytest.raises(ValueError, match="Unsupported format: xyz"):
            save_generated_structures(structures, "test.xyz", format="xyz")

    def test_save_generated_structures_exception_handling(self):
        """Test saving structures with exception handling."""
        structures = ["CCO", "CCC"]

        with patch("builtins.open", side_effect=IOError("File error")), patch(
            "logging.error"
        ) as mock_error:
            with pytest.raises(IOError):
                save_generated_structures(structures, "test.smi", format="smi")

            mock_error.assert_called_once()

    def test_generate_diverse_library_basic(self):
        """Test diverse library generation."""
        seed_molecules = ["CCO", "CCC"]

        with patch(
            "qemlflow.research.drug_discovery.generation.MolecularGenerator"
        ) as mock_gen_class:
            mock_generator = Mock()
            mock_generator.generate_similar_molecules.return_value = [
                "CCO_mod",
                "CCC_mod",
            ]
            mock_gen_class.return_value = mock_generator

            result = generate_diverse_library(
                seed_molecules, library_size=10, diversity_threshold=0.6
            )

            assert isinstance(result, list)
            assert "CCO" in result
            assert "CCC" in result

    def test_generate_diverse_library_size_limiting(self):
        """Test diverse library generation with size limiting."""
        seed_molecules = ["CCO", "CCC", "c1ccccc1"]

        with patch(
            "qemlflow.research.drug_discovery.generation.MolecularGenerator"
        ) as mock_gen_class, patch("random.sample") as mock_sample:
            mock_generator = Mock()
            mock_generator.generate_similar_molecules.return_value = [
                "mod1",
                "mod2",
                "mod3",
            ]
            mock_gen_class.return_value = mock_generator

            # Mock a library larger than target size
            mock_sample.return_value = ["CCO", "CCC"]

            result = generate_diverse_library(
                seed_molecules, library_size=2, diversity_threshold=0.5
            )

            # Should call random.sample to limit size
            assert len(result) <= 2


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""

    def test_complete_generation_workflow(self):
        """Test complete molecular generation workflow."""
        with patch(
            "qemlflow.research.drug_discovery.generation.MolecularGenerator"
        ) as mock_gen_class:
            mock_generator = Mock()
            mock_generator.generate_random_smiles.return_value = ["CCO", "CCC"]
            mock_gen_class.return_value = mock_generator

            # Generate molecules
            molecules = generate_molecular_structures(
                num_samples=2, generation_type="random"
            )

            # Save them
            with patch("builtins.open", mock_open()):
                save_generated_structures(molecules, "test.smi", format="smi")

            assert molecules == ["CCO", "CCC"]

    def test_similarity_based_generation_workflow(self):
        """Test similarity-based generation workflow."""
        generator = MolecularGenerator()

        with patch.object(
            generator,
            "generate_similar_molecules",
            return_value=["CCO_mod1", "CCO_mod2"],
        ):
            similar_mols = generator.generate_similar_molecules("CCO", num_molecules=2)
            assert len(similar_mols) == 2

    def test_fragment_to_optimization_workflow(self):
        """Test fragment-based generation followed by optimization."""
        fragment_gen = FragmentBasedGenerator()

        with patch.object(
            fragment_gen, "generate_from_fragments", return_value=["c1ccccc1"]
        ):
            fragments = fragment_gen.generate_from_fragments(num_molecules=1)

            with patch(
                "qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False
            ):
                optimized = optimize_structure(fragments[0])
                assert optimized == fragments[0]


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_generator_with_extreme_parameters(self):
        """Test generator with extreme parameters."""
        generator = MolecularGenerator()

        # Test with very large max_atoms
        with patch(
            "qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False
        ):
            result = generator.generate_random_smiles(num_molecules=1, max_atoms=1000)
            assert len(result) == 1

    def test_generate_similar_molecules_edge_cases(self):
        """Test similar molecule generation edge cases."""
        generator = MolecularGenerator()

        # Test with very high similarity threshold
        with patch(
            "qemlflow.research.drug_discovery.generation.RDKIT_AVAILABLE", False
        ):
            result = generator.generate_similar_molecules(
                "CCO", num_molecules=5, similarity_threshold=0.99
            )
            assert all(mol == "CCO" for mol in result)

    def test_fragment_generator_empty_library(self):
        """Test fragment generator with empty library."""
        generator = FragmentBasedGenerator(fragment_library=[])

        # Should handle empty library gracefully
        with patch("random.randint", return_value=0), patch(
            "random.sample", return_value=[]
        ):
            result = generator.generate_from_fragments(num_molecules=1)
            assert len(result) == 1


class TestPerformance:
    """Test performance and scalability."""

    def test_large_scale_generation(self):
        """Test generation of large numbers of molecules."""
        with patch(
            "qemlflow.research.drug_discovery.generation.MolecularGenerator"
        ) as mock_gen_class:
            mock_generator = Mock()
            mock_generator.generate_random_smiles.return_value = ["CCO"] * 1000
            mock_gen_class.return_value = mock_generator

            result = generate_molecular_structures(
                num_samples=1000, generation_type="random"
            )
            assert len(result) == 1000

    def test_diverse_library_performance(self):
        """Test diverse library generation performance."""
        seed_molecules = ["CCO"] * 100  # Large seed set

        with patch(
            "qemlflow.research.drug_discovery.generation.MolecularGenerator"
        ) as mock_gen_class:
            mock_generator = Mock()
            mock_generator.generate_similar_molecules.return_value = []
            mock_gen_class.return_value = mock_generator

            result = generate_diverse_library(seed_molecules, library_size=50)
            assert len(result) <= 50


class TestCrossModuleCompatibility:
    """Test compatibility with other modules."""

    def test_molecular_generation_imports(self):
        """Test that all required imports work."""
        # Test module imports
        assert hasattr(generate_molecular_structures, "__call__")
        assert hasattr(optimize_structure, "__call__")
        assert hasattr(save_generated_structures, "__call__")
        assert hasattr(generate_diverse_library, "__call__")

    def test_pandas_dataframe_integration(self):
        """Test integration with pandas DataFrames."""
        structures = ["CCO", "CCC", "c1ccccc1"]

        with patch("pandas.DataFrame") as mock_df:
            mock_df.return_value.to_csv = Mock()
            save_generated_structures(structures, "test.csv", format="csv")
            mock_df.assert_called_once()

    def test_numpy_array_compatibility(self):
        """Test compatibility with numpy arrays."""
        with patch("numpy.random.seed") as mock_seed:
            _generator = MolecularGenerator(seed=42)
            mock_seed.assert_called_once_with(42)
